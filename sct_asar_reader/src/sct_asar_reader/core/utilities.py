# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""Envisat & ERS reader support module."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import epr
import numpy as np
from epr import Dataset, EPRTime, Record
from numpy.polynomial import Polynomial
from numpy.typing import ArrayLike
from perseo_core.geometry.geocoding import direct_geocoding_monostatic
from perseo_core.geometry.navigation import CubicSplineTrajectory, Trajectory
from perseo_core.timing import PreciseDateTime
from scipy.constants import speed_of_light
from scipy.interpolate import CubicSpline

from sct_asar_reader.core.common import (
    ConversionFunction,
    ConversionPolynomial,
    DatasetInfo,
    DopplerEvaluator,
    OrbitDirection,
    PulseInfo,
    RasterInfo,
    RasterInfoAxis,
    SARPolarization,
    SARProjection,
    SARRadiometricQuantity,
    SARSamplingFrequencies,
    StandardSARAcquisitionMode,
)

_DATA_EXTENSIONS = [".N1", ".E1", ".E2"]
MPH_SIZE = 1247

unit_of_measure_removal_re = re.compile("<.*>")


class InvalidASARProductError(RuntimeError):
    """Invalid ASAR product error"""


class UnsupportedASARProductAcquisitionModeError(RuntimeError):
    """Current product acquisition mode is not supported"""


class ASARProductType(Enum):
    """ASAR Product Types"""

    SLC = "SLC"
    GRD = "GROUND RANGE"

    @classmethod
    def from_str(cls, name: str) -> ASARProductType:
        """Associating correct enum value to product type.

        Parameters
        ----------
        name : str
            product type

        Returns
        -------
        ASARProductType
            product type corresponding to the input product type
        """
        if name.upper() == "COMPLEX":
            return cls.SLC
        return cls.GRD


class ASARAcquisitionMode(Enum):
    """ASAR Product Acquisition Modes"""

    STRIPMAP = auto()
    WAVE = auto()

    @classmethod
    def from_str(cls, name: str) -> ASARAcquisitionMode:
        """Associating correct enum value to product name.

        Parameters
        ----------
        name : str
            product name

        Returns
        -------
        ASARAcquisitionMode
            acquisition mode corresponding to the input product name
        """
        parts = name.split("_")
        if "IM" in parts[1]:
            # Image Mode
            return cls.STRIPMAP
        if "AP" in parts[1]:
            # Alternated Polarization
            return cls.STRIPMAP
        if "WSM" in parts[1] and "1P" in parts[2]:
            # Wide Swath Medium Resolution Image
            return cls.STRIPMAP
        raise UnsupportedASARProductAcquisitionModeError(f"Unsupported acquisition mode type {name}")


def mjd_datetime_converter(epr_time: EPRTime) -> PreciseDateTime:
    """Converts EPRTime class in Modified Julian Date (MJD) 2000 format to PreciseDateTime.

    Parameters
    ----------
    epr_time : EPRTime
        EPRTime to be converted

    Returns
    -------
    PreciseDateTime
        corresponding PreciseDateTime object
    """

    return (
        PreciseDateTime.from_numeric_datetime(year=2000)
        + epr_time.days * 24 * 60 * 60
        + epr_time.seconds
        + epr_time.microseconds * 1e-6
    )


def raster_info_from_record(
    main_params_dataset: Dataset, geolocation_record: Record, product_type: ASARProductType
) -> RasterInfo:
    """Generating RasterInfo object from metadata.

    Parameters
    ----------
    main_params_dataset : Dataset
        main processing parameters Dataset object
    geolocation_record : Record
        geolocation Record object
    product_type : ASARProductType
        product type

    Returns
    -------
    RasterInfo
        RasterInfo object
    """
    main_params_records = [m for m in main_params_dataset]
    lines = sum([m.get_field("num_output_lines").get_elem() for m in main_params_records])

    if product_type == ASARProductType.SLC:
        celltype = "FLOAT_COMPLEX"
        samples_start = geolocation_record.get_field("first_line_tie_points.slant_range_times").get_elem() / 1e9
        samples_unit = "s"
        samples_step = 1 / main_params_records[0].get_field("range_samp_rate").get_elem()
    else:
        celltype = "FLOAT32"
        samples_start = 0
        samples_unit = "m"
        samples_step = main_params_records[0].get_field("range_spacing").get_elem()

    raster_lines = RasterInfoAxis(
        length=lines,
        start=mjd_datetime_converter(main_params_records[0].get_field("first_zero_doppler_time").get_elem()),
        step=main_params_records[0].get_field("line_time_interval").get_elem(),
        step_unit="s",
    )
    raster_samples = RasterInfoAxis(
        length=main_params_dataset.read_record(0).get_field("num_samples_per_line").get_elem(),
        start=samples_start,
        step=samples_step,
        step_unit=samples_unit,
    )

    return RasterInfo(
        lines=raster_lines,
        samples=raster_samples,
        data_type=celltype,
    )


def dataset_info_from_record(
    product_type: ASARProductType,
    acquisition_mode: ASARAcquisitionMode,
    main_params_record: Record,
    mph: ASARMainProductHeader,
    sph: ASARSpecificProductHeader,
) -> DatasetInfo:
    """Creating a DataSetInfo object from metadata.

    Parameters
    ----------
    product_type : ASARProductType
        ASAR product type
    acquisition_mode : ASARAcquisitionMode
        ASAR acquisition mode
    main_params_record : Record
        main processing parameters Record object
    mph : ASARMainProductHeader
        ASAR main product header
    sph : ASARSpecificProductHeader
        ASAR specific product header

    Returns
    -------
    DataSetInfo
        DataSetInfo metadata object
    """
    return DatasetInfo(
        fc_hz=main_params_record.get_field("radar_freq").get_elem(),
        acquisition_mode=acquisition_mode.name,
        image_type="AZIMUTH FOCUSED" if product_type == ASARProductType.SLC else "MULTILOOK",
        projection=product_type.value,
        sensor_name="ASAR",
        side_looking="RIGHT",
    )


def sampling_constants_from_record(main_params_record: Record) -> SARSamplingFrequencies:
    """Creating a SARSamplingFrequencies object from metadata.

    Parameters
    ----------
    main_params_record : Record
        main processing parameters Record object

    Returns
    -------
    SARSamplingFrequencies
        SARSamplingFrequencies metadata object
    """
    return SARSamplingFrequencies(
        azimuth_bandwidth_freq_hz=1 / main_params_record.get_field("line_time_interval").get_elem(),
        azimuth_freq_hz=1 / main_params_record.get_field("line_time_interval").get_elem(),
        range_bandwidth_freq_hz=main_params_record.get_field("bandwidth.tot_bw_range").get_elem(),
        range_freq_hz=main_params_record.get_field("range_samp_rate").get_elem(),
    )


def pulse_info_from_record(main_params_record: Record) -> PulseInfo:
    """Creating a Pulse object from metadata.

    Parameters
    ----------
    main_params_record : Record
        main processing parameters Record object

    Returns
    -------
    PulseInfo
        Pulse metadata object
    """
    chirp_bandwidth = main_params_record.get_field("bandwidth.tot_bw_range").get_elem()
    chirp_length = 1  # TODO: understand where to get it!
    return PulseInfo(
        length_s=chirp_length,
        bandwidth_hz=chirp_bandwidth,
        energy_j=-1,
        sampling_rate_hz=main_params_record.get_field("range_samp_rate").get_elem(),
        start_frequency_hz=-chirp_bandwidth / 2,
        start_phase=(np.pi * chirp_bandwidth * chirp_length / 4) % (2 * np.pi),
        direction="UP",
    )


def doppler_centroid_poly_from_dataset(dc_params_dataset: Dataset) -> DopplerEvaluator:
    """Creating a DopplerCentroid SortedPolyList object from metadata.

    Parameters
    ----------
    dc_params_dataset : Dataset
        Doppler Centroid parameters Dataset object

    Returns
    -------
    DopplerEvaluator
        Doppler Centroid evaluator object
    """
    doppler_poly = []
    az_ref_times = []
    for dc_params in dc_params_dataset:
        az_ref_time = mjd_datetime_converter(dc_params.get_field("zero_doppler_time").get_elem())
        coefficients = dc_params.get_field("dop_coef").get_elems()
        az_ref_times.append(az_ref_time)
        doppler_poly.append(
            ConversionFunction(
                azimuth_reference_time=az_ref_time,
                origin=dc_params.get_field("slant_range_time").get_elem() / 1e9,
                function=Polynomial(coefficients),
            )
        )

    return DopplerEvaluator(functions=doppler_poly, azimuth_reference_times=np.array(az_ref_times))


def doppler_rate_poly_from_dataset(main_params_dataset: Dataset) -> DopplerEvaluator:
    """Creating a DopplerRate SortedPolyList object from metadata.

    Parameters
    ----------
    main_params_dataset : Dataset
        main processing parameters Dataset object

    Returns
    -------
    DopplerEvaluator
        Doppler Rate evaluator object
    """

    doppler_poly = []
    az_ref_times = []
    for main_params in main_params_dataset:
        az_ref_time = mjd_datetime_converter(main_params.get_field("first_zero_doppler_time").get_elem())
        coefficients = main_params.get_field("az_fm_rate").get_elems()
        az_ref_times.append(az_ref_time)
        doppler_poly.append(
            ConversionFunction(
                azimuth_reference_time=az_ref_time,
                origin=main_params.get_field("ax_fm_origin").get_elem() / 1e9,
                function=Polynomial(coefficients),
            )
        )

    return DopplerEvaluator(functions=doppler_poly, azimuth_reference_times=np.array(az_ref_times))


def orbit_from_state_vectors(state_vectors: ASARStateVectors) -> CubicSplineTrajectory:
    """Creating a Trajectory object from ASARStateVectors data.

    Parameters
    ----------
    state_vectors : ASARStateVectors
        state vectors data

    Returns
    -------
    CubicSplineTrajectory
        CubicSplineTrajectory object
    """
    return CubicSplineTrajectory(
        times=state_vectors.time_axis, positions=state_vectors.positions, velocities=state_vectors.velocities
    )


def _remove_unit_of_measure(text: str) -> str:
    """Removing unit of measure indicated by <unit-of-measure> from product header field values.

    Parameters
    ----------
    text : str
        text containing unit of measures

    Returns
    -------
    str
        text without unit of measure
    """
    return unit_of_measure_removal_re.sub("", text)


def read_product_headers(product: str | Path) -> tuple[ASARMainProductHeader, ASARSpecificProductHeader]:
    """Reading Main Product Header (MPH) and Specific Product Header (SPH) from ASAR product.

    Parameters
    ----------
    product : str | Path
        path to ASAR product

    Returns
    -------
    ASARMainProductHeader
        main product header
    ASARSpecificProductHeader
        specific product header
    """
    with open(product, "rb") as f_in:
        mph_content = ASARMainProductHeader.from_bytes(header_bytes=f_in.read(MPH_SIZE))
        sph_content = ASARSpecificProductHeader.from_bytes(header_bytes=f_in.read(mph_content.sph_size_bytes))

    return mph_content, sph_content


def generate_channel_names(swath: str, polarizations: list[SARPolarization]) -> list[str]:
    """Generating channel names as 'swath_pol' based on Swath and Polarization values.

    Parameters
    ----------
    swath : str
        swath name
    polarizations : list[SARPolarization]
        list of polarizations

    Returns
    -------
    list[str]
        list of channel names
    """
    return [swath.lower() + "_" + pol.name.lower() for pol in polarizations]


def get_projection_from_product_type(product_type: ASARProductType) -> SARProjection:
    """Get SAR Projection from ASAR Product Type.

    Parameters
    ----------
    product_type : ASARProductType
        ASAR product type

    Returns
    -------
    SARProjection
        data projection
    """
    if product_type == ASARProductType.SLC:
        return SARProjection.SLANT_RANGE
    return SARProjection.GROUND_RANGE


def get_calibration_factor(index: int, main_params_record: Record) -> float:
    """Get calibration factor from metadata.

    Parameters
    ----------
    index : int
        index of dataset
    main_params_record : Record
        main processing parameters Record object

    Returns
    -------
    float
        calibration factor
    """
    calibration_factor_fields = [f for f in main_params_record.get_field_names() if "calibration_factors" in f]
    ext_cal_fields = [f for f in calibration_factor_fields if "ext_cal" in f]
    calibration_factors = [main_params_record.get_field(f).get_elem() for f in ext_cal_fields]
    return 1 / np.sqrt(calibration_factors[index])


@dataclass
class ASARMainProductHeader:
    """ASAR product Main Product Header (MPH)"""

    product: str
    processing_stage: str
    reference_doc: str
    acquisition_station: str
    processing_center: str
    processing_time: PreciseDateTime
    software_version: str
    sensing_start: PreciseDateTime
    sensing_stop: PreciseDateTime
    phase: int
    cycle: int
    relative_orbit: int
    absolute_orbit: int
    state_vector_time: PreciseDateTime
    delta_ut1_s: float
    position: np.ndarray
    velocity: np.ndarray
    vector_source: str
    utc_sbt_time: PreciseDateTime
    satellite_binary_time: int
    clock_step_ps: int
    leap_utc: PreciseDateTime
    leap_sign: int
    leap_error: int
    product_error: int
    total_size_bytes: int
    sph_size_bytes: int
    dataset_descriptors_num: int
    dataset_descriptors_size_bytes: int
    datasets_num: int

    @classmethod
    def from_bytes(cls, header_bytes: bytes) -> ASARMainProductHeader:
        """Generating an ASARMainProductHeader class from corresponding header bytes.

        Parameters
        ----------
        header_bytes : bytes
            bytes read fro product corresponding to the MPH

        Returns
        -------
        ASARMainProductHeader
            ASARMainProductHeader object
        """

        raw_content = [p.strip() for p in header_bytes.decode().split("\n") if p.strip()]
        content_dict = {
            key: _remove_unit_of_measure(val.replace('"', "").strip())
            for (key, val) in [p.split("=") for p in raw_content]
        }
        position = np.array(
            [float(content_dict["X_POSITION"]), float(content_dict["Y_POSITION"]), float(content_dict["Z_POSITION"])]
        )
        velocity = np.array(
            [float(content_dict["X_VELOCITY"]), float(content_dict["Y_VELOCITY"]), float(content_dict["Z_VELOCITY"])]
        )
        return cls(
            product=content_dict["PRODUCT"],
            processing_stage=content_dict["PROC_STAGE"],
            reference_doc=content_dict["REF_DOC"],
            acquisition_station=content_dict["ACQUISITION_STATION"],
            processing_center=content_dict["PROC_CENTER"],
            processing_time=PreciseDateTime.from_utc_string(content_dict["PROC_TIME"]),
            software_version=content_dict["SOFTWARE_VER"],
            sensing_start=PreciseDateTime.from_utc_string(content_dict["SENSING_START"]),
            sensing_stop=PreciseDateTime.from_utc_string(content_dict["SENSING_STOP"]),
            phase=content_dict["PHASE"],
            cycle=int(content_dict["CYCLE"]),
            relative_orbit=int(content_dict["REL_ORBIT"]),
            absolute_orbit=int(content_dict["ABS_ORBIT"]),
            state_vector_time=PreciseDateTime.from_utc_string(content_dict["STATE_VECTOR_TIME"]),
            delta_ut1_s=float(content_dict["DELTA_UT1"]),
            position=position,
            velocity=velocity,
            vector_source=content_dict["VECTOR_SOURCE"],
            utc_sbt_time=PreciseDateTime.from_utc_string(content_dict["UTC_SBT_TIME"]),
            satellite_binary_time=int(content_dict["SAT_BINARY_TIME"]),
            clock_step_ps=int(content_dict["CLOCK_STEP"]),
            leap_utc=PreciseDateTime.from_utc_string(content_dict["LEAP_UTC"]),
            leap_sign=int(content_dict["LEAP_SIGN"]),
            leap_error=int(content_dict["LEAP_ERR"]),
            product_error=int(content_dict["PRODUCT_ERR"]),
            total_size_bytes=int(content_dict["TOT_SIZE"]),
            sph_size_bytes=int(content_dict["SPH_SIZE"]),
            dataset_descriptors_num=int(content_dict["NUM_DSD"]),
            dataset_descriptors_size_bytes=int(content_dict["DSD_SIZE"]),
            datasets_num=int(content_dict["NUM_DATA_SETS"]),
        )


@dataclass
class ASARSpecificProductHeader:
    """ASAR product Specific Product Header (SPH)"""

    sph_descriptor: str
    stripline_continuity_indicator: int
    slice_position: int
    number_of_slices: int
    first_line_time: PreciseDateTime
    last_line_time: PreciseDateTime
    swath: str
    orbit_direction: OrbitDirection
    sample_type: str
    algorithm: str
    mds_polarizations: list[SARPolarization]
    compression: str
    azimuth_looks: int
    range_looks: int
    range_spacing_m: float
    azimuth_spacing_m: float
    line_time_interval_s: float
    samples: int
    data_type: str
    latitudes: np.ndarray
    longitudes: np.ndarray

    @classmethod
    def from_bytes(cls, header_bytes: bytes) -> ASARSpecificProductHeader:
        """Generating an ASARSpecificProductHeader class from corresponding header bytes.

        Parameters
        ----------
        header_bytes : bytes
            bytes read fro product corresponding to the SPH

        Returns
        -------
        ASARSpecificProductHeader
            ASARSpecificProductHeader object
        """
        raw_content = [p.strip() for p in header_bytes.decode().split("\n") if p.strip()]
        content_dict = {
            key: _remove_unit_of_measure(val.replace('"', "").strip())
            for (key, val) in [p.split("=") for p in raw_content]
        }
        return cls(
            sph_descriptor=content_dict["SPH_DESCRIPTOR"],
            stripline_continuity_indicator=int(content_dict["STRIPLINE_CONTINUITY_INDICATOR"]),
            slice_position=int(content_dict["SLICE_POSITION"]),
            number_of_slices=int(content_dict["NUM_SLICES"]),
            first_line_time=PreciseDateTime.from_utc_string(content_dict["FIRST_LINE_TIME"]),
            last_line_time=PreciseDateTime.from_utc_string(content_dict["LAST_LINE_TIME"]),
            swath=content_dict["SWATH"],
            orbit_direction=OrbitDirection(content_dict["PASS"].lower()),
            sample_type=content_dict["SAMPLE_TYPE"],
            algorithm=content_dict["ALGORITHM"],
            mds_polarizations=[SARPolarization(val) for c, val in content_dict.items() if ("TX_RX_POLAR" in c and val)],
            compression=content_dict["COMPRESSION"],
            azimuth_looks=int(content_dict["AZIMUTH_LOOKS"]),
            range_looks=int(content_dict["RANGE_LOOKS"]),
            range_spacing_m=float(content_dict["RANGE_SPACING"]),
            azimuth_spacing_m=float(content_dict["AZIMUTH_SPACING"]),
            line_time_interval_s=float(content_dict["LINE_TIME_INTERVAL"]),
            samples=float(content_dict["LINE_LENGTH"]),
            data_type=content_dict["DATA_TYPE"],
            latitudes=np.array([float(val) / 1e6 for key, val in content_dict.items() if "_LAT" in key]),
            longitudes=np.array([float(val) / 1e6 for key, val in content_dict.items() if "_LONG" in key]),
        )


@dataclass
class ASARSwathInfo:
    """ASAR swath info"""

    rank: int
    azimuth_steering_rate_poly: tuple[float, float, float]
    prf: float

    @classmethod
    def from_record(cls, main_params_record: Record) -> ASARSwathInfo:
        """Generating ASARSwathInfo object from metadata.

        Parameters
        ----------
        main_params_record : Record
            main processing parameters Record object

        Returns
        -------
        ASARSwathInfo
            swath info dataclass
        """
        return cls(
            rank=0,  # TODO: check if correct
            azimuth_steering_rate_poly=(0, 0, 0),  # TODO: check if correct
            prf=main_params_record.get_field("image_parameters.prf_value").get_elem(),
        )


@dataclass
class ASARStateVectors:
    """ASAR orbit's state vectors"""

    num: int
    positions: np.ndarray
    velocities: np.ndarray
    time_axis: np.ndarray
    time_step: float
    orbit_direction: OrbitDirection

    @classmethod
    def from_metadata(cls, main_params_dataset: Record, orbit_direction: OrbitDirection) -> ASARStateVectors:
        """Generating a ASARStateVectors object from metadata.

        Parameters
        ----------
        main_params_dataset : Dataset
            main processing parameters Dataset object
        orbit_direction : OrbitDirection
            orbit direction

        Returns
        -------
        ASARStateVectors
            orbit's state vectors
        """
        state_vectors_fields = [
            f for f in main_params_dataset.read_record(0).get_field_names() if "orbit_state_vectors" in f
        ]
        time_fields = sorted([f for f in state_vectors_fields if "state_vect_time" in f])
        position_fields = sorted([f for f in state_vectors_fields if "_pos_" in f])
        velocity_fields = sorted([f for f in state_vectors_fields if "_vel_" in f])

        time_axis = []
        positions_x, positions_y, positions_z = [], [], []
        velocities_x, velocities_y, velocities_z = [], [], []
        # gathering state vectors data from all slices
        for main_params in main_params_dataset:
            time_axis.extend([mjd_datetime_converter(main_params.get_field(f).get_elem()) for f in time_fields])
            positions_x.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-2 for f in position_fields if "x_" in f]
            )
            positions_y.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-2 for f in position_fields if "y_" in f]
            )
            positions_z.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-2 for f in position_fields if "z_" in f]
            )
            velocities_x.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-5 for f in velocity_fields if "x_" in f]
            )
            velocities_y.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-5 for f in velocity_fields if "y_" in f]
            )
            velocities_z.extend(
                [float(main_params.get_field(f).get_elem()) * 1e-5 for f in velocity_fields if "z_" in f]
            )

        time_axis = np.array(time_axis)
        assert time_axis.size == len(positions_x) == len(positions_y) == len(positions_z)
        assert time_axis.size == len(velocities_x) == len(velocities_y) == len(velocities_z)

        # interpolating state vectors if more than one slice
        if main_params_dataset.get_num_records() > 1:
            start_time = time_axis[0]
            relative_time_axis = (time_axis - start_time).astype(float)
            interpolated_relative_time_axis = np.linspace(0, relative_time_axis[-1], num=relative_time_axis.size)
            interpolated_positions_x = np.interp(interpolated_relative_time_axis, relative_time_axis, positions_x)
            interpolated_positions_y = np.interp(interpolated_relative_time_axis, relative_time_axis, positions_y)
            interpolated_positions_z = np.interp(interpolated_relative_time_axis, relative_time_axis, positions_z)
            interpolated_velocities_x = np.interp(interpolated_relative_time_axis, relative_time_axis, velocities_x)
            interpolated_velocities_y = np.interp(interpolated_relative_time_axis, relative_time_axis, velocities_y)
            interpolated_velocities_z = np.interp(interpolated_relative_time_axis, relative_time_axis, velocities_z)
            time_axis = interpolated_relative_time_axis + start_time
            positions = np.c_[interpolated_positions_x, interpolated_positions_y, interpolated_positions_z]
            velocities = np.c_[interpolated_velocities_x, interpolated_velocities_y, interpolated_velocities_z]
        else:
            positions = np.c_[positions_x, positions_y, positions_z]
            velocities = np.c_[velocities_x, velocities_y, velocities_z]

        return cls(
            num=time_axis.size,
            positions=positions,
            velocities=velocities,
            time_axis=time_axis,
            time_step=float(time_axis[1] - time_axis[0]),
            orbit_direction=orbit_direction,
        )


@dataclass
class ASARBurstInfo:
    """ASAR burst info"""

    num: int  # number of bursts in this swath
    lines_per_burst: int  # number of azimuth lines within each burst
    samples_per_burst: int  # number of range samples within each burst
    azimuth_start_times: np.ndarray  # zero doppler azimuth time of the first line of this burst
    range_start_times: np.ndarray  # zero doppler range time of the first sample of this burst

    @classmethod
    def from_metadata(cls, record: Record) -> ASARBurstInfo:
        """Generating SAOCOMBurstInfo object directly from metadata xml node.

        Parameters
        ----------
        node : etree._Element
            BurstInfo metadata node
        samples : int
            number of samples per burst

        Returns
        -------
        SAOCOMBurstInfo
            swath's burst info dataclass
        """
        # TODO: implement real burst info object, is it needed?
        ...


@dataclass
class ASARCoordinateConversions:
    """ASAR coordinate conversion"""

    ground_to_slant: list[ConversionPolynomial] | None = None
    slant_to_ground: list[ConversionPolynomial] | None = None
    azimuth_reference_times: np.ndarray | None = None

    def _detect_right_polynomial_index(self, azimuth_time: PreciseDateTime) -> int:
        """Detecting the index of the right polynomial to be used given an input azimuth time.
        The polynomial to be used is the one with reference azimuth time closest to the input value but with
        reference_azimuth_time < input_azimuth_time.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            selected azimuth time

        Returns
        -------
        int
            index corresponding to the polynomial to be used
        """
        diff = np.array(azimuth_time - self.azimuth_reference_times).astype("float")
        return np.ma.masked_where(diff < 0, diff).argmin()

    @classmethod
    def from_dataset(cls, slant_to_ground_dataset: Dataset, raster_info: RasterInfo) -> ASARCoordinateConversions:
        """Generating ASARCoordinateConversions object from metadata.

        Parameters
        ----------
        slant_to_ground_dataset : Dataset
            slant to ground Dataset metadata object
        raster_info : RasterInfo
            product raster info metadata object

        Returns
        -------
        ASARCoordinateConversions
            polynomial for coordinate conversion dataclass
        """
        ground_to_slant_poly_list, slant_to_ground_poly_list, az_ref_times = [], [], []
        range_axis = np.arange(0, (raster_info.samples.length + 1) * raster_info.samples.step, raster_info.samples.step)
        for poly_data in slant_to_ground_dataset:
            az_ref_time = mjd_datetime_converter(poly_data.get_field("zero_doppler_time").get_elem())
            ground_to_slant_poly = Polynomial(poly_data.get_field("srgr_coeff").get_elems())
            ground_to_slant_poly_evaluated = ground_to_slant_poly(range_axis) / (speed_of_light / 2)
            slant_to_ground_spline = CubicSpline(ground_to_slant_poly_evaluated, range_axis)
            az_ref_times.append(az_ref_time)
            ground_to_slant_poly_list.append(
                ConversionPolynomial(
                    azimuth_reference_time=az_ref_time,
                    origin=poly_data.get_field("ground_range_origin").get_elem(),
                    polynomial=ground_to_slant_poly,
                )
            )
            slant_to_ground_poly_list.append(
                ConversionPolynomial(
                    azimuth_reference_time=az_ref_time,
                    origin=0,
                    polynomial=slant_to_ground_spline,
                )
            )

        return cls(
            azimuth_reference_times=np.array(az_ref_times),
            ground_to_slant=ground_to_slant_poly_list,
            slant_to_ground=slant_to_ground_poly_list,
        )

    @classmethod
    def from_orbit(cls, orbit: Trajectory, raster_info: RasterInfo) -> ASARCoordinateConversions:
        """Generating ASARCoordinateConversions object from orbit and direct geocoding grid.

        Parameters
        ----------
        orbit : Trajectory
            sensor orbit
        raster_info : RasterInfo
            product raster info metadata object

        Returns
        -------
        ASARCoordinateConversions
            polynomial for coordinate conversion dataclass
        """
        mid_azimuth = raster_info.lines.start + raster_info.lines.length * raster_info.lines.step / 2
        range_times = np.arange(0, raster_info.samples.length, 1) * raster_info.samples.step + raster_info.samples.start
        ground_points = direct_geocoding_monostatic(
            sensor_positions=orbit.position(mid_azimuth),
            sensor_velocities=orbit.velocity(mid_azimuth),
            range_times=range_times,
            doppler_frequencies=0,
            wavelength=1,
            look_direction="RIGHT",
            altitude=0,
        )
        ground_points_distances = np.linalg.norm(np.diff(ground_points, axis=0), axis=1)
        ground_range_axis = np.r_[[0], np.cumsum(ground_points_distances)]
        slant_to_ground_poly = Polynomial.fit(x=range_times, y=ground_range_axis, deg=8)
        ground_to_slant_poly_list = Polynomial.fit(x=ground_range_axis, y=range_times, deg=8)

        return cls(
            azimuth_reference_times=np.array(raster_info.lines.start),
            ground_to_slant=ConversionPolynomial(
                azimuth_reference_time=raster_info.lines.start, origin=0, polynomial=ground_to_slant_poly_list
            ),
            slant_to_ground=ConversionPolynomial(
                azimuth_reference_time=raster_info.lines.start, origin=0, polynomial=slant_to_ground_poly
            ),
        )

    def evaluate_ground_to_slant(self, azimuth_time: PreciseDateTime, ground_range: ArrayLike) -> float:
        """Compute ground to slant conversion.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time to select the proper polynomial to be used for conversion
        ground_range :  ArrayLike
            ground range value(s) in meters

        Returns
        -------
        float
            slant range value
        """
        poly_index = self._detect_right_polynomial_index(azimuth_time=azimuth_time)
        poly = self.ground_to_slant[poly_index]
        return poly.polynomial(ground_range - poly.origin) / (speed_of_light / 2)

    def evaluate_slant_to_ground(self, azimuth_time: PreciseDateTime, slant_range: ArrayLike) -> float:
        """Compute slant to ground conversion.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time to select the proper polynomial to be used for conversion
        slant_range :  ArrayLike
            slant range value(s) in seconds

        Returns
        -------
        float
            ground range value
        """
        poly_index = self._detect_right_polynomial_index(azimuth_time=azimuth_time)
        poly = self.slant_to_ground[poly_index]
        return poly.polynomial(slant_range - poly.origin)


@dataclass
class ASARGeneralChannelInfo:
    """ASAR general channel info dataclass"""

    product_name: str
    channel_id: str
    swath: str
    product_type: ASARProductType
    polarization: SARPolarization
    projection: SARProjection
    acquisition_mode: ASARAcquisitionMode
    acquisition_mode_std: StandardSARAcquisitionMode
    orbit_direction: OrbitDirection
    signal_frequency: float
    acq_start_time: PreciseDateTime
    acq_stop_time: PreciseDateTime


@dataclass
class ASARChannelMetadata:
    """ASAR channel metadata dataclass"""

    general_info: ASARGeneralChannelInfo
    orbit: Trajectory
    image_calibration_factor: float
    image_radiometric_quantity: SARRadiometricQuantity
    burst_info: ASARBurstInfo
    raster_info: RasterInfo
    dataset_info: DatasetInfo
    swath_info: ASARSwathInfo
    sampling_constants: SARSamplingFrequencies
    # acquisition_timeline: meta.AcquisitionTimeLine
    doppler_centroid_poly: DopplerEvaluator
    doppler_rate_poly: DopplerEvaluator
    pulse: PulseInfo
    coordinate_conversions: ASARCoordinateConversions
    state_vectors: ASARStateVectors


class ASARProduct:
    """ASAR product object"""

    def __init__(self, path: str | Path) -> None:
        """ASAR Product init from directory path.

        Parameters
        ----------
        path : str | Path
            path to ASAR product
        """
        _path = Path(path)
        self._product_path = _path
        self._product_name = self._product_path.name

        mph, sph = read_product_headers(product=self._product_path)
        self._channels_list = generate_channel_names(swath=sph.swath, polarizations=sph.mds_polarizations)

        # channels list and number
        self._channels_number = len(self._channels_list)

        # retrieve acquisition time
        self._acq_time = mph.sensing_start

        # retrieve scene footprint
        self._footprint = (sph.latitudes.min(), sph.latitudes.max(), sph.longitudes.min(), sph.longitudes.max())

    @property
    def acquisition_time(self) -> PreciseDateTime:
        """Acquisition start time for this product"""
        return self._acq_time

    @property
    def channels_number(self) -> int:
        """Returning the number of channels of ASAR product"""
        return self._channels_number

    @property
    def channels_list(self) -> list[str]:
        """Returning the list of channels"""
        return self._channels_list

    @property
    def footprint(self) -> tuple[float, float, float, float]:
        """Product footprint as tuple of (min lat, max lat, min lon, max lon)"""
        return self._footprint


def is_asar_product(product: str | Path) -> bool:
    """Check if input path corresponds to a valid ASAR product, basic version.

    Conditions to be met for basic validity:
        - path exists
        - path is a .N1 file
        - open file and read product headers (MPH, SPH)

    Parameters
    ----------
    product : str | Path
        path to the product to be checked

    Returns
    -------
    bool
        True if it is a valid product, else False
    """
    product = Path(product)

    if not product.exists():
        return False

    extensions_check = [str(product).endswith(e) for e in _DATA_EXTENSIONS]
    if not any(extensions_check):
        return False

    # open product, read acquisition mode
    try:
        root = epr.open(str(product))
        read_product_headers(product=product)
    except Exception:
        return False
    finally:
        root.close()

    return True
