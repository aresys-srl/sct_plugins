# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Biomass product format PERSEO-Quality protocol-compliant wrapper
--------------------------------------------------------------------
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from arepytools.geometry.generalsarattitude import (
    create_attitude_boresight_normal_curve_wrapper,
    create_general_sar_attitude,
)
from arepytools.geometry.geometric_functions import (
    compute_ground_velocity_from_trajectory,
    compute_incidence_angles_from_trajectory,
    compute_look_angles_from_trajectory,
)
from arepytools.geometry.inverse_geocoding_core import inverse_geocoding_monostatic_core
from arepytools.io.create_orbit import create_orbit
from arepytools.io.metadata import BurstInfo, RasterInfo, SamplingConstants
from arepytools.math.genericpoly import SortedPolyList, create_sorted_poly_list
from bps.transcoder.sarproduct.biomass_l1product_reader import (
    BIOMASSL1Product,
    BIOMASSL1ProductReader,
)
from perseo_quality.core.generic_dataclasses import (
    LocationData,
    SARAcquisitionMode,
    SARImageType,
    SAROrbitDirection,
    SARPolarization,
    SARProjection,
    SARRadiometricQuantity,
    SARSamplingFrequencies,
    SARSideLooking,
)
from perseo_quality.core.signal_processing import radiometric_correction
from perseo_quality.io.layout import L1BurstLayout, L1RasterLayout
from perseo_quality.io.protocol_utilities import roi_validation
from scipy.constants import speed_of_light
from shapely import Polygon

if TYPE_CHECKING:
    from arepytools.geometry.curve import Generic3DCurve
    from arepytools.geometry.orbit import Orbit
    from arepytools.timing.precisedatetime import PreciseDateTime
    from numpy.typing import ArrayLike


def raster_layout_from_metadata(burst_info: BurstInfo, raster_info: RasterInfo) -> L1RasterLayout:
    """Generating a L1RasterLayout from Product Folder BurstInfo and RasterInfo metadata for the current channel.

    Parameters
    ----------
    burst_info : BurstInfo
        channel BurstInfo
    raster_info : RasterInfo
        channel RasterInfo

    Returns
    -------
    L1RasterLayout
        raster layout of current Product Folder channel
    """
    bursts_layout = []
    for brst_id in range(burst_info.get_number_of_bursts()):
        burst = burst_info.get_burst(brst_id)
        assert isinstance(raster_info.samples_start, float)
        bursts_layout.append(
            L1BurstLayout(
                burst_id=brst_id,
                lines=burst.lines,
                samples=raster_info.samples,
                lines_start=burst.azimuth_start_time,
                lines_step=raster_info.lines_step,
                samples_start=raster_info.samples_start,
                samples_step=raster_info.samples_step,
            ),
        )
    return L1RasterLayout(lines=raster_info.lines, samples=raster_info.samples, bursts=bursts_layout)


def _get_raster_layout(bursts: list[L1BurstLayout]) -> tuple[list[list[PreciseDateTime]], list[list[float]]]:
    """Evaluating raster boundaries taking into account the bursts, if needed.

    Returns
    -------
    tuple[list[list[PreciseDateTime]], list[list[float]]]
        azimuth raster boundaries (azimuth start, azimuth stop),
        range raster boundaries (range start, range stop)
    """

    burst_az_boundaries: list[list[PreciseDateTime]] = [[b.azimuth_axis[0], b.azimuth_axis[-1]] for b in bursts]
    burst_rng_boundaries: list[list[float]] = [[b.range_axis[0], b.range_axis[-1]] for b in bursts]

    return burst_az_boundaries, burst_rng_boundaries


class DopplerPolynomialWrapper:
    """Generic Polynomial wrapper used to interpolate Doppler data (Doppler Centroid or Rate)"""

    def __init__(self, sorted_poly: SortedPolyList) -> None:
        self._sorted_poly = sorted_poly

    def evaluate(self, azimuth_time: PreciseDateTime, range_time: float) -> float:
        """Evaluate the Doppler Polynomial at given azimuth and range times.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time at which evaluate the polynomial
        range_time : float
            range time at which evaluate the polynomial

        Returns
        -------
        float
            doppler at that time
        """
        return self._sorted_poly.evaluate((azimuth_time, range_time))


class BiomassL1ProductManager:
    """Biomass product Manager class satisfying the QualityInputProduct protocol"""

    def __init__(self, path: str | Path, **kwargs) -> None:
        self._product_path = Path(path)
        self._product = BIOMASSL1ProductReader(path).read()

    @property
    def path(self) -> Path:
        """Get product path"""
        return self._product_path

    @property
    def name(self) -> str:
        """Get product name"""
        assert self._product.name is not None
        return self._product.name

    @property
    def channels_list(self) -> list[int]:
        """Get list of available channels for this product"""
        return list(range(len(self._product.data_list)))

    def get_channel_data(self, channel_id: int) -> BiomassChannelManager:
        """Get data and info referring to the selected channel"""
        return BiomassChannelManager(product=self._product, channel_num=channel_id)

    @property
    def footprint(self) -> Polygon:
        """Get product scene footprint as a Shapely Polygon"""
        footprint = np.stack(self._product.footprint)
        min_lat, min_lon = footprint.min(axis=0)
        max_lat, max_lon = footprint.max(axis=0)
        boundaries = [min_lat, max_lat, min_lon, max_lon]
        region_corners = list(itertools.product(boundaries[:2], boundaries[2:]))
        return Polygon(region_corners).convex_hull


def _sampling_frequencies_from_metadata(sampling_constants: SamplingConstants) -> SARSamplingFrequencies:
    """Generating a SARSamplingFrequencies dataclass from Product Folder SamplingConstants metadata.

    Parameters
    ----------
    sampling_constants : SamplingConstants
        channel SamplingConstants

    Returns
    -------
    SARSamplingFrequencies
        sampling frequencies of current Product Folder channel
    """
    assert sampling_constants.baz_hz is not None
    assert sampling_constants.brg_hz is not None
    assert sampling_constants.faz_hz is not None
    assert sampling_constants.frg_hz is not None
    return SARSamplingFrequencies(
        range_freq_hz=sampling_constants.frg_hz,
        azimuth_freq_hz=sampling_constants.faz_hz,
        range_bandwidth_freq_hz=sampling_constants.brg_hz,
        azimuth_bandwidth_freq_hz=sampling_constants.baz_hz,
    )


class BiomassChannelManager:
    """Channel Manager class satisfying the ChannelData protocol"""

    def __init__(self, product: BIOMASSL1Product, channel_num: int) -> None:
        """Creating a ChannelManager object compliant with the ChannelData protocol."""
        self._channel_num = channel_num
        self._channel_raster = product.data_list[channel_num]
        self._raster_info = product.raster_info_list[channel_num]
        self._swath_info = product.swath_info_list[channel_num]
        self._dataset_info = product.dataset_info[0]
        self._burst_info = product.burst_info_list[channel_num]
        self._pulse = product.pulse_list[channel_num]
        self._acquisition_time_line = product.acquisition_timeline_list[channel_num]
        self._g2s_poly = create_sorted_poly_list(product.ground_to_slant_list[channel_num])
        self._s2g_poly = create_sorted_poly_list(product.slant_to_ground_list[channel_num])
        self._signal_constants = _sampling_frequencies_from_metadata(product.sampling_constants_list[channel_num])

        centroid_poly = product.dc_vector_list[channel_num]
        self._doppler_centroid_poly = (
            DopplerPolynomialWrapper(sorted_poly=create_sorted_poly_list(centroid_poly))
            if centroid_poly.get_number_of_poly() > 0
            else None
        )

        rate_poly = product.dr_vector_list[channel_num]
        self._doppler_rate_poly = (
            DopplerPolynomialWrapper(sorted_poly=create_sorted_poly_list(rate_poly))
            if rate_poly.get_number_of_poly() > 0
            else None
        )

        self._raster_layout = raster_layout_from_metadata(burst_info=self._burst_info, raster_info=self._raster_info)

        self._orbit_direction = SAROrbitDirection[product.general_sar_orbit[0].orbit_direction.value]

        self._trajectory_rx = create_orbit(state_vectors=product.general_sar_orbit[0])
        self._trajectory_tx = None

        self._boresight_normal = create_attitude_boresight_normal_curve_wrapper(
            attitude=create_general_sar_attitude(
                product.general_sar_orbit[0],
                attitude_info=product.attitude_info[0],
                ignore_anx_after_orbit_start=True,
            )
        )

    @property
    def sensor_name(self) -> str:
        """Name of the sensor"""
        return "BIOMASS"

    @property
    def swath_name(self) -> str:
        """Name of the swath being analyzed"""
        assert self._swath_info.swath is not None
        return self._swath_info.swath

    @property
    def channel_id(self) -> int:
        """Number corresponding to the current channel data"""
        return self._channel_num

    @property
    def prf(self) -> float:
        """Sensor Pulse Repetition Frequency (PRF)"""
        return self._swath_info.acquisition_prf

    @property
    def range_step_m(self) -> float:
        """Step along range direction, in meters"""
        if self.projection == SARProjection.GROUND_RANGE:
            return self._raster_info.samples_step
        return self._raster_info.samples_step * speed_of_light / 2

    @property
    def azimuth_step_s(self) -> float:
        """Step along azimuth direction, in seconds"""
        return self._raster_info.lines_step

    @property
    def projection(self) -> SARProjection:
        """Channel data projection"""
        return SARProjection(self._dataset_info.projection)

    @property
    def polarization(self) -> SARPolarization:
        """Channel data polarization"""
        return SARPolarization(self._swath_info.polarization.value)

    @property
    def acquisition_mode(self) -> SARAcquisitionMode:
        """Channel data acquisition mode"""
        return SARAcquisitionMode.STRIPMAP

    @property
    def orbit_direction(self) -> SAROrbitDirection:
        """Channel data orbit direction"""
        return self._orbit_direction

    @property
    def image_type(self) -> SARImageType:
        """Channel raster image type"""
        assert self._dataset_info.image_type is not None
        return SARImageType.from_str(self._dataset_info.image_type)

    @property
    def sampling_constants(self) -> SARSamplingFrequencies:
        """Channel data signal sampling frequencies"""
        return self._signal_constants

    @property
    def looking_side(self) -> SARSideLooking:
        """Sensor look direction for this channel"""
        assert self._dataset_info.side_looking is not None
        return SARSideLooking(self._dataset_info.side_looking.value.upper())

    @property
    def carrier_frequency(self) -> float:
        """Signal carrier frequency"""
        assert self._dataset_info.fc_hz is not None
        return self._dataset_info.fc_hz

    @property
    def mid_azimuth_time(self) -> PreciseDateTime:
        """Azimuth time at half swath"""
        return self._raster_layout.mid_swath_azimuth

    @property
    def trajectory(self) -> Orbit:
        """Channel trajectory 3D curve"""
        return self._trajectory_rx

    @property
    def boresight_normal_curve(self) -> Generic3DCurve | None:
        """Channel attitude boresight normal 3D curve"""
        return self._boresight_normal

    @property
    def doppler_centroid(self) -> DopplerPolynomialWrapper | None:
        """Channel doppler centroid polynomial wrapper"""
        return self._doppler_centroid_poly

    @property
    def doppler_rate(self) -> DopplerPolynomialWrapper | None:
        """Channel doppler rate polynomial wrapper"""
        return self._doppler_rate_poly

    @property
    def mid_range_time(self) -> float:
        """Range time at half swath"""
        if self.projection == SARProjection.GROUND_RANGE:
            return self._g2s_poly.evaluate(
                (
                    self._raster_layout.mid_swath_azimuth,
                    np.floor(self._raster_layout.mid_swath_range),
                ),
            )

        return self._raster_layout.mid_swath_range

    @property
    def range_axis(self) -> np.ndarray:
        """Range axis"""
        return self._raster_layout.raster_range_axis

    @property
    def slant_range_axis(self) -> np.ndarray:
        """Slant Range axis"""
        if self.projection == SARProjection.GROUND_RANGE:
            return self._g2s_poly.evaluate(
                (
                    self._raster_layout.mid_swath_azimuth,
                    self._raster_layout.raster_range_axis,
                ),
            )

        return self._raster_layout.raster_range_axis

    @property
    def azimuth_axis(self) -> np.ndarray:
        """Azimuth axis, PreciseDateTime format"""
        return self._raster_layout.raster_azimuth_axis

    @property
    def lines_per_burst(self) -> np.ndarray:
        """Lines per burst, for each burst in the swath"""
        return np.array([self._raster_info.lines])

    @property
    def radiometric_quantity(self) -> SARRadiometricQuantity:
        """Product radiometric quantity"""
        if self._dataset_info.image_quantity == "BETA":
            return SARRadiometricQuantity.BETA_NOUGHT
        if self._dataset_info.image_quantity == "GAMMA":
            return SARRadiometricQuantity.GAMMA_NOUGHT
        if self._dataset_info.image_quantity == "SIGMA":
            return SARRadiometricQuantity.SIGMA_NOUGHT

        return SARRadiometricQuantity.BETA_NOUGHT

    def get_mid_burst_times(self, burst: int) -> tuple[PreciseDateTime, float]:
        """Compute mid azimuth and range times for a given burst.

        Returns
        -------
        tuple(PreciseDateTime, float)
            azimuth and range mid burst times
        """
        selected_burst = self._raster_layout.get_burst_layout(burst_id=burst)
        return selected_burst.mid_burst_azimuth, selected_burst.mid_burst_range

    def get_steering_rate(self, azimuth_time: PreciseDateTime, burst: int) -> float:
        """Compute steering rate at a given azimuth time and for a given burst."""
        return 0.0

    def get_location_data(self, azimuth_time: PreciseDateTime, range_time: float) -> LocationData:
        """Generating a LocationData object containing data and info derived from the current ChannelManager and
        declined to the specific azimuth and range times selected.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            selected azimuth time
        range_time : float
            selected range time

        Returns
        -------
        LocationData
            LocationData instance related to the selected location
        """

        incidence_angle = compute_incidence_angles_from_trajectory(
            trajectory=self.trajectory,
            azimuth_time=azimuth_time,
            range_times=range_time,
            look_direction=self.looking_side.value,
        )
        # TODO compute look angles/ground velocity directly at target position and not a mid range
        look_angle = compute_look_angles_from_trajectory(
            trajectory=self.trajectory,
            azimuth_time=azimuth_time,
            range_times=self.mid_range_time,
            look_direction=self.looking_side.value,
        )
        v_ground = compute_ground_velocity_from_trajectory(
            trajectory=self.trajectory,
            azimuth_time=azimuth_time,
            look_angles_rad=look_angle,
        )
        azimuth_step_m = self.azimuth_step_s * v_ground

        if self.projection == SARProjection.SLANT_RANGE:
            ground_range_step_m: float = self.range_step_m / np.sin(incidence_angle)
            range_step_m = self.range_step_m
        else:
            assert self.projection == SARProjection.GROUND_RANGE
            ground_range_step_m: float = self.range_step_m
            range_step_m = self.range_step_m * np.sin(incidence_angle)

        return LocationData(
            abs_azimuth_time=azimuth_time,
            abs_range_time=range_time,
            incidence_angle=incidence_angle,
            look_angle=look_angle,
            ground_velocity=v_ground,
            azimuth_step_m=azimuth_step_m,
            range_step_m=range_step_m,
            ground_range_step_m=ground_range_step_m,
        )

    def pixel_to_times_conversion(
        self,
        azimuth_index: float,
        range_index: float,
        burst: int | None = None,
    ) -> tuple[PreciseDateTime, float]:
        """Converting input raster pixel coordinates (azimuth_index and range index) to corresponding absolute times,
        azimuth and range.

        Parameters
        ----------
        azimuth_index : float
            azimuth pixel index, subpixel precision
        range_index : float
            range pixel index, subpixel precision
        burst : int, optional
            burst index, by default None

        Returns
        -------
        PreciseDateTime
            azimuth time
        float
            range time
        """

        az_time = self._raster_layout.pixel_to_azimuth_conversion(az_pixel_index=azimuth_index)
        rng_time = self._raster_layout.pixel_to_range_conversion(rng_pixel_index=range_index)

        if self.projection == SARProjection.GROUND_RANGE:
            rng_time = self._g2s_poly.evaluate((self.mid_azimuth_time, rng_time))

        return az_time, rng_time

    def times_to_pixel_conversion(
        self,
        azimuth_time: PreciseDateTime,
        range_time: float,
        burst: int | None = None,
    ) -> tuple[float, float]:
        """Converting azimuth and range times to raster image pixels indexes with subpixel precision.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time
        range_time : float
            range time
        burst : int
            burst number corresponding to these times

        Returns
        -------
        float
            pixel corresponding to azimuth time
        float
            pixel corresponding to range time
        """

        azmth_idx = self._raster_layout.azimuth_to_pixel_conversion(az=azimuth_time, burst_id=burst)
        if self.projection == SARProjection.GROUND_RANGE:
            range_time = self._s2g_poly.evaluate((azimuth_time, range_time))
        rng_idx = self._raster_layout.range_to_pixel_conversion(rng=range_time, burst_id=burst)
        # TODO: forcing only first burst match
        return azmth_idx[0][1], rng_idx[0][1]

    def ground_points_to_burst_association(self, coordinates: ArrayLike) -> list[list[int] | None]:
        """Determining the burst (or bursts) where the input coordinates lie. If no association can be found (i.e. the
        point is not visible in the scene), None is returned.

        Parameters
        ----------
        coordinates : ArrayLike
            array of coordinates, in the form (N, 3)

        Returns
        -------
        list[[list[int] | None]]
            list containing the burst association for each input point, None if no association was found
        """

        coordinates = np.atleast_2d(coordinates)

        burst_az_boundaries, burst_rng_boundaries = _get_raster_layout(self._raster_layout.bursts)

        bursts = []
        for point in coordinates:
            try:
                t_azmth, t_rng = inverse_geocoding_monostatic_core(
                    trajectory=self.trajectory,
                    ground_points=point,
                    wavelength=1,
                    frequencies_doppler_centroid=0,
                    initial_guesses=self.mid_azimuth_time,
                )

                az_check: list[bool] = [az[0] < t_azmth < az[1] for az in burst_az_boundaries]
                rng_check: list[bool] = [rng[0] < t_rng < rng[1] for rng in burst_rng_boundaries]
                check = np.logical_and(az_check, rng_check)
                if check.any():
                    bursts.append(list(np.where(check)[0]))
                else:
                    bursts.append(None)
            except Exception:
                bursts.append(None)

        return bursts

    def times_to_burst_association(self, azimuth_times: ArrayLike) -> list[int]:
        """Associate the right burst to a given input time point. This function returns 1 association for each
        input time.
        Associating time only to the first burst containing it."""
        return [0] * len(azimuth_times)

    def pixel_to_burst_association(self, azimuth_px_indexes: ArrayLike) -> list[int]:
        """Associate the azimuth pixel value to the right burst. This function returns 1 association for each
        input time."""
        return [0] * len(azimuth_px_indexes)

    def read_data(
        self,
        azimuth_index: int,
        range_index: int,
        cropping_size: tuple[int, int] = (150, 150),
        output_radiometric_quantity: SARRadiometricQuantity = SARRadiometricQuantity.BETA_NOUGHT,
        burst: int | None = None,
    ) -> np.ndarray:
        """Extracting the swath portion centered to the provided target position and of size cropping_size by
        cropping_size. Target position is provided via its azimuth and range indexes in the swath array.

        Parameters
        ----------
        azimuth_index : int
            index of azimuth time in swath array
        range_index : int
            index of range time in swath array
        cropping_size : tuple[int, int], optional
            size in pixel of the swath portion to be read (number of samples, number of lines), by default (150, 150)
        output_radiometric_quantity : SARRadiometricQuantity, optional
            selected output radiometric quantity to convert the read data to, if needed,
            by default SARRadiometricQuantity.BETA_NOUGHT
        burst : int, optional
            if burst is provided, the roi extraction gives error if the boundaries exceed the burst boundaries,
            by default None

        Returns
        -------
        np.ndarray
            cropped swath array centered to the input target coordinates, data is provided with shape (samples, lines)
            by default the output radiometric quantity is BETA_NOUGHT, unless specified otherwise

        Raises
        ------
        AzimuthExceedsBoundariesError
            azimuth index exceeds swath or burst boundaries
        RangeExceedsBoundariesError
            range index exceeds swath or burst boundaries
        """
        target_block = [
            azimuth_index - np.floor(cropping_size[1] / 2).astype(int),
            range_index - np.floor(cropping_size[0] / 2).astype(int),
            cropping_size[1],
            cropping_size[0],
        ]

        roi_validation(
            roi=target_block,
            raster_boundaries=[
                0,
                0,
                self._raster_layout.lines,
                self._raster_layout.samples,
            ],
            burst_boundaries=None,
        )

        data = self._channel_raster[
            target_block[0] : target_block[0] + target_block[2],
            target_block[1] : target_block[1] + target_block[3],
        ].T

        if self.radiometric_quantity != output_radiometric_quantity:
            azimuth_time, _ = self.pixel_to_times_conversion(azimuth_index=azimuth_index, range_index=range_index)
            incidence_angles = compute_incidence_angles_from_trajectory(
                trajectory=self.trajectory,
                azimuth_time=azimuth_time,
                range_times=self.slant_range_axis[target_block[1] : target_block[1] + target_block[3]],
                look_direction=self.looking_side.value,
            )
            data = radiometric_correction(
                data=data,
                incidence_angle=incidence_angles,
                input_quantity=self.radiometric_quantity,
                output_quantity=output_radiometric_quantity,
            )

        return data
