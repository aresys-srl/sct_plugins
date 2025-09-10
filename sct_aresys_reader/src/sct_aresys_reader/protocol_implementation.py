# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Aresys product format PERSEO-Quality protocol-compliant wrapper
--------------------------------------------------------------------
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
from arepytools.geometry.conversions import xyz2llh
from arepytools.geometry.curve import Generic3DCurve
from arepytools.geometry.direct_geocoding import direct_geocoding_monostatic
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
from arepytools.geometry.orbit import Orbit
from arepytools.io import (
    open_product_folder,
    read_metadata,
    read_raster_with_raster_info,
)
from arepytools.io.create_orbit import create_orbit
from arepytools.io.metadata import BurstInfo, RasterInfo
from arepytools.math.genericpoly import SortedPolyList, create_sorted_poly_list
from arepytools.timing.precisedatetime import PreciseDateTime
from numpy.typing import ArrayLike
from perseo_quality.core.custom_errors import (
    CoordinatesOutOfBounds,
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


def raster_layout_from_metadata(burst_info: BurstInfo | None, raster_info: RasterInfo) -> L1RasterLayout:
    """Generating a L1RasterLayout from Product Folder BurstInfo and RasterInfo metadata for the current channel.

    Parameters
    ----------
    burst_info : BurstInfo | None
        channel BurstInfo, None if not present
    raster_info : RasterInfo
        channel RasterInfo

    Returns
    -------
    L1RasterLayout
        raster layout of current Product Folder channel
    """
    if burst_info is None:
        burst_info = BurstInfo()
        burst_info.add_burst(
            azimuth_start_time_i=raster_info.lines_start,
            range_start_time_i=raster_info.samples_start,
            lines_i=raster_info.lines,
        )
    bursts_layout = []
    for brst_id in range(burst_info.get_number_of_bursts()):
        burst = burst_info.get_burst(brst_id)
        bursts_layout.append(
            L1BurstLayout(
                burst_id=brst_id,
                lines=burst.lines,
                samples=raster_info.samples,
                lines_start=burst.azimuth_start_time,
                lines_step=raster_info.lines_step,
                samples_start=raster_info.samples_start,
                samples_step=raster_info.samples_step,
            )
        )
    return L1RasterLayout(lines=raster_info.lines, samples=raster_info.samples, bursts=bursts_layout)


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


class ProductFolderManager:
    """Product Manager class satisfying the QualityInputProduct protocol"""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._product_name = self._path.name
        self._product = open_product_folder(self._path)
        self._channel_list = self._product.get_channels_list()

    @property
    def path(self) -> Path:
        """Get product path"""
        return self._path

    @property
    def name(self) -> str:
        """Get product name"""
        return self._product_name

    @property
    def channels_list(self) -> list[int]:
        """Get list of available channels for this product"""
        return self._channel_list

    def get_channel_data(self, channel_id: int) -> ChannelManager:
        """Get data and info referring to the selected channel.

        Parameters
        ----------
        channel_id : int
            selected channel number

        Returns
        -------
        ChannelManager
            ChannelManager containing data corresponding to the selected channel
        """
        metadata = self._product.get_channel_metadata(channel_id)
        raster = self._product.get_channel_data(channel_id)
        return ChannelManager(channel_metadata_path=metadata, channel_raster_path=raster, channel_num=channel_id)


class ProductFolderManagerExtended(ProductFolderManager):
    def __init__(self, path: str | Path, **kwargs) -> None:
        super().__init__(path)

    def _compute_footprint(self) -> Polygon:
        """Computing Product Folder scene footprint considering all channels.

        Returns
        -------
        Polygon
            Polygon object corresponding to the Product Folder lat/lon scene footprint
        """
        footprint_corners = []
        for channel_id in self._channel_list:
            metadata = read_metadata(self._product.get_channel_metadata(channel_id))
            dataset_info = metadata.get_dataset_info()
            burst_info = metadata.get_burst_info()
            raster_info = metadata.get_raster_info()
            trajectory = create_orbit(state_vectors=metadata.get_state_vectors())

            if burst_info is not None:
                first_burst = burst_info.get_burst(0)
                last_burst = burst_info.get_burst(burst_info.get_number_of_bursts() - 1)
                corners_az = [
                    last_burst.azimuth_start_time + last_burst.lines * raster_info.lines_step,
                    last_burst.azimuth_start_time + last_burst.lines * raster_info.lines_step,
                    first_burst.azimuth_start_time,
                    first_burst.azimuth_start_time,
                ]
            else:
                corners_az = [
                    raster_info.lines_start + raster_info.lines * raster_info.lines_step,
                    raster_info.lines_start + raster_info.lines * raster_info.lines_step,
                    raster_info.lines_start,
                    raster_info.lines_start,
                ]

            corners_rng = [
                raster_info.samples_start,
                raster_info.samples_start + raster_info.samples * raster_info.samples_step,
                raster_info.samples_start + raster_info.samples * raster_info.samples_step,
                raster_info.samples_start,
            ]
            if dataset_info.projection == "GROUND RANGE":
                gts_poly = metadata.get_ground_to_slant()
                corners_rng = [
                    create_sorted_poly_list(gts_poly).evaluate((raster_info.lines_start, r)) for r in corners_rng
                ]

            for az, rng in zip(corners_az, corners_rng, strict=True):
                corner_xyz = direct_geocoding_monostatic(
                    sensor_positions=trajectory.evaluate(az),
                    sensor_velocities=trajectory.evaluate_first_derivatives(az),
                    range_times=rng,
                    frequencies_doppler_centroid=0,
                    wavelength=1,
                    geodetic_altitude=0,
                    geocoding_side=dataset_info.side_looking.value,
                )
                corner_llh = xyz2llh(corner_xyz).squeeze()
                footprint_corners.append(np.rad2deg(corner_llh[:2]))

        footprint = np.stack(footprint_corners)
        min_lat, min_lon = footprint.min(axis=0)
        max_lat, max_lon = footprint.max(axis=0)
        boundaries = [min_lat, max_lat, min_lon, max_lon]
        region_corners = list(product(boundaries[:2], boundaries[2:]))
        return Polygon(region_corners)

    @property
    def footprint(self) -> Polygon | None:
        """Get product scene footprint as a Shapely Polygon"""
        return self._compute_footprint()


class ChannelManager:
    """Channel Manager class satisfying the ChannelData protocol"""

    def __init__(self, channel_metadata_path: Path, channel_raster_path: Path, channel_num: int) -> None:
        """Creating a ChannelManager object compliant with the ChannelData protocol.

        Parameters
        ----------
        channel_metadata_path : Path
            Path to the channel metadata xml file
        channel_raster_path : int
            Path to the channel raster file
        channel_num : int
            number of current channel
        """
        self._channel_num = channel_num
        self._channel_raster = channel_raster_path
        self._channel_metadata = read_metadata(channel_metadata_path)
        self._state_vectors = self._channel_metadata.get_state_vectors()
        self._raster_info = self._channel_metadata.get_raster_info()
        self._swath_info = self._channel_metadata.get_swath_info()
        self._dataset_info = self._channel_metadata.get_dataset_info()
        self._attitude_info = self._channel_metadata.get_attitude_info()
        self._burst_info = self._channel_metadata.get_burst_info()
        self._pulse = self._channel_metadata.get_pulse()
        self._acquisition_time_line = self._channel_metadata.get_acquisition_time_line()
        self._g2s_poly = create_sorted_poly_list(self._channel_metadata.get_ground_to_slant())
        self._s2g_poly = create_sorted_poly_list(self._channel_metadata.get_slant_to_ground())

        # setting image radiometric quantity
        if self._dataset_info.image_quantity == "BETA":
            self._radiometric_quantity = SARRadiometricQuantity.BETA_NOUGHT
        elif self._dataset_info.image_quantity == "GAMMA":
            self._radiometric_quantity = SARRadiometricQuantity.GAMMA_NOUGHT
        elif self._dataset_info.image_quantity == "SIGMA":
            self._radiometric_quantity = SARRadiometricQuantity.SIGMA_NOUGHT
        else:
            self._radiometric_quantity = SARRadiometricQuantity.BETA_NOUGHT

        # setting acquisition mode
        if self._dataset_info.acquisition_mode == "SCANSAR":
            self._acq_mode = SARAcquisitionMode.SCANSAR
        elif self._dataset_info.acquisition_mode == "SPOT" or self._dataset_info.acquisition_mode == "SPOTLIGHT":
            self._acq_mode = SARAcquisitionMode.SPOTLIGHT
        elif self._dataset_info.acquisition_mode == "STRIPMAP":
            self._acq_mode = SARAcquisitionMode.STRIPMAP
        elif self._dataset_info.acquisition_mode == "TOPSAR":
            self._acq_mode = SARAcquisitionMode.TOPSAR
        elif self._dataset_info.acquisition_mode == "WAVE":
            self._acq_mode = SARAcquisitionMode.WAVE

        # re-arranging signal sampling frequencies
        self._sensor_name = "" if self._dataset_info.sensor_name is None else self._dataset_info.sensor_name
        self._sampling_constants = self._channel_metadata.get_sampling_constants()
        self._signal_constants = SARSamplingFrequencies(
            range_freq_hz=self._sampling_constants.frg_hz,
            azimuth_freq_hz=self._sampling_constants.faz_hz,
            range_bandwidth_freq_hz=self._sampling_constants.brg_hz,
            azimuth_bandwidth_freq_hz=self._sampling_constants.baz_hz,
        )
        self._prf = self._swath_info.acquisition_prf

        # creating doppler centroid and rate polynomial wrappers
        centroid_poly = self._channel_metadata.get_doppler_centroid()
        rate_poly = self._channel_metadata.get_doppler_rate()
        self._doppler_centroid_poly = (
            DopplerPolynomialWrapper(sorted_poly=create_sorted_poly_list(centroid_poly))
            if centroid_poly.get_number_of_poly() > 0
            else None
        )
        self._doppler_rate_poly = (
            DopplerPolynomialWrapper(sorted_poly=create_sorted_poly_list(rate_poly))
            if rate_poly.get_number_of_poly() > 0
            else None
        )
        # retrieving azimuth steering rate polynomial coefficients
        self._steering_rate_poly_coeff = self._swath_info.azimuth_steering_rate_pol

        # swath and main parameters
        self._swath = self._swath_info.swath
        self._product_folder_image_type = SARImageType.from_str(self._dataset_info.image_type)
        self._channel_projection = SARProjection(self._dataset_info.projection)
        self._polarization = SARPolarization(self._swath_info.polarization.value)
        self._orbit_direction = SAROrbitDirection[self._state_vectors.orbit_direction.value]
        self._looking_side = SARSideLooking(self._dataset_info.side_looking.value.upper())
        self._carrier_freq = self._dataset_info.fc_hz

        # layout
        raster_layout = raster_layout_from_metadata(burst_info=self._burst_info, raster_info=self._raster_info)
        self._azimuth_axis = raster_layout.raster_azimuth_axis
        self._az_time_half_swath = raster_layout.mid_swath_azimuth
        self._range_axis = raster_layout.raster_range_axis
        self._slant_range_axis = raster_layout.raster_range_axis
        self._rng_time_half_swath = raster_layout.mid_swath_range
        self._az_step_s = self._raster_info.lines_step
        self._range_step_m = self._raster_info.samples_step * speed_of_light / 2
        if self._channel_projection == SARProjection.GROUND_RANGE:
            self._rng_time_half_swath = self._g2s_poly.evaluate(
                (self._az_time_half_swath, np.floor(self._rng_time_half_swath))
            )
            self._slant_range_axis = self._g2s_poly.evaluate((self._az_time_half_swath, self._range_axis))
            self._range_step_m = self._raster_info.samples_step
        self._lines_per_burst_array = np.array(
            [raster_layout.get_burst_lines(burst_id=b) for b in raster_layout.burst_ids]
        )
        self._raster_layout = raster_layout

        # generating trajectory
        self._trajectory_rx = create_orbit(state_vectors=self._state_vectors)
        self._trajectory_tx = None

        # generating attitude boresight normal curve
        self._boresight_normal = None
        if self._attitude_info is not None:
            self._attitude = create_general_sar_attitude(
                self._state_vectors, attitude_info=self._attitude_info, ignore_anx_after_orbit_start=True
            )
            self._boresight_normal = create_attitude_boresight_normal_curve_wrapper(attitude=self._attitude)

    def _get_raster_layout(self) -> tuple[list[PreciseDateTime], list[float]]:
        """Evaluating raster boundaries taking into account the bursts, if needed.

        Returns
        -------
        tuple[list[list[PreciseDateTime, PreciseDateTime]], list[list[float, float]]]
            azimuth raster boundaries (azimuth start, azimuth stop),
            range raster boundaries (range start, range stop)
        """

        burst_az_boundaries = [[b.azimuth_axis[0], b.azimuth_axis[-1]] for b in self._raster_layout.bursts]
        burst_rng_boundaries = [[b.range_axis[0], b.range_axis[-1]] for b in self._raster_layout.bursts]

        return burst_az_boundaries, burst_rng_boundaries

    @property
    def sensor_name(self) -> str:
        """Name of the sensor"""
        return self._sensor_name

    @property
    def swath_name(self) -> str:
        """Name of the swath being analyzed"""
        return self._swath

    @property
    def channel_id(self) -> int:
        """Number corresponding to the current channel data"""
        return self._channel_num

    @property
    def prf(self) -> float:
        """Sensor Pulse Repetition Frequency (PRF)"""
        return self._prf

    @property
    def range_step_m(self) -> float:
        """Step along range direction, in meters"""
        return self._range_step_m

    @property
    def azimuth_step_s(self) -> float:
        """Step along azimuth direction, in seconds"""
        return self._az_step_s

    @property
    def projection(self) -> SARProjection:
        """Channel data projection"""
        return self._channel_projection

    @property
    def polarization(self) -> SARPolarization:
        """Channel data polarization"""
        return self._polarization

    @property
    def acquisition_mode(self) -> SARAcquisitionMode:
        """Channel data acquisition mode"""
        return self._acq_mode

    @property
    def orbit_direction(self) -> SAROrbitDirection:
        """Channel data orbit direction"""
        return self._orbit_direction

    @property
    def image_type(self) -> SARImageType:
        """Channel raster image type"""
        return self._product_folder_image_type

    @property
    def sampling_constants(self) -> SARSamplingFrequencies:
        """Channel data signal sampling frequencies"""
        return self._signal_constants

    @property
    def looking_side(self) -> SARSideLooking:
        """Sensor look direction for this channel"""
        return self._looking_side

    @property
    def carrier_frequency(self) -> float:
        """Signal carrier frequency"""
        return self._carrier_freq

    @property
    def mid_azimuth_time(self) -> PreciseDateTime:
        """Azimuth time at half swath"""
        return self._az_time_half_swath

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
        return self._rng_time_half_swath

    @property
    def range_axis(self) -> np.ndarray:
        """Range axis"""
        return self._range_axis

    @property
    def slant_range_axis(self) -> np.ndarray:
        """Slant Range axis"""
        return self._slant_range_axis

    @property
    def azimuth_axis(self) -> np.ndarray:
        """Azimuth axis, PreciseDateTime format"""
        return self._azimuth_axis

    @property
    def lines_per_burst(self) -> np.ndarray:
        """Lines per burst, for each burst in the swath"""
        return self._lines_per_burst_array

    @property
    def radiometric_quantity(self) -> np.ndarray:
        """Product radiometric quantity"""
        return self._radiometric_quantity

    # TODO: is this still needed? exposing layout would remove a lot of properties...
    def get_mid_burst_times(self, burst: int) -> tuple[PreciseDateTime, float]:
        """Compute mid azimuth and range times for a given burst.

        Returns
        -------
        tuple(PreciseDateTime, float)
            azimuth and range mid burst times
        """
        selected_burst = self._raster_layout.get_burst_layout(burst_id=burst)
        return selected_burst.mid_burst_azimuth, selected_burst.mid_burst_range

    # TODO: setup a polynomial manager as per doppler centroid and doppler rate
    def get_steering_rate(self, azimuth_time: PreciseDateTime, burst: int) -> float:
        """Compute steering rate at a given azimuth time and for a given burst.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time
        burst : int
            burst corresponding to the input time

        Returns
        -------
        float
            azimuth steering rate
        """
        time_rel = azimuth_time - self._raster_layout.raster_azimuth_axis[0]
        return (
            self._steering_rate_poly_coeff[0]
            + self._steering_rate_poly_coeff[1] * time_rel
            + self._steering_rate_poly_coeff[2] * time_rel**2
        )

    def get_location_data(self, azimuth_time: PreciseDateTime, range_time: float) -> LocationData:
        """Generating a LocationData object containing data and info derived from the current ChannelManager and
        declined to the specific azimuth and range times selected.

        Parameters
        ----------
        abs_azimuth_time : PreciseDateTime
            selected absolute azimuth time
        abs_range_time : float
            selected absolute range time

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
            trajectory=self.trajectory, azimuth_time=azimuth_time, look_angles_rad=look_angle
        )
        azimuth_step_m = self.azimuth_step_s * v_ground

        if self.projection == SARProjection.SLANT_RANGE:
            ground_range_step_m: float = self.range_step_m / np.sin(incidence_angle)
            range_step_m = self.range_step_m
        elif self.projection == SARProjection.GROUND_RANGE:
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
        self, azimuth_index: float, range_index: float, burst: int = None
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

        # TODO: remove burst input
        az_time = self._raster_layout.pixel_to_azimuth_conversion(az_pixel_index=azimuth_index)
        rng_time = self._raster_layout.pixel_to_range_conversion(rng_pixel_index=range_index)

        if self.projection == SARProjection.GROUND_RANGE:
            rng_time = self._g2s_poly.evaluate((self.mid_azimuth_time, rng_time))

        return az_time, rng_time

    def times_to_pixel_conversion(
        self, azimuth_time: PreciseDateTime, range_time: float, burst: int = None
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

        burst_az_boundaries, burst_rng_boundaries = self._get_raster_layout()

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

                az_check = [(t_azmth < az[1] and t_azmth > az[0]) for az in burst_az_boundaries]
                rng_check = [(t_rng < rng[1] and t_rng > rng[0]) for rng in burst_rng_boundaries]
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
        Associating time only to the first burst containing it.

        Parameters
        ----------
        azimuth_time : ArrayLike
            azimuth time array in PreciseDateTime format

        Returns
        -------
        list[int]
            burst associated with a given time

        Raises
        ------
        CoordinatesOutOfBounds
            if input time exceeds tme boundaries of the swath
        """
        if self._channel.burst_info is None:
            return [0] * len(azimuth_times)

        bursts_start_times = [
            self._burst_info.get_azimuth_start_time(b) for b in range(self._burst_info.get_number_of_bursts())
        ]
        last_time = (
            bursts_start_times[0]
            + self._burst_info.get_number_of_bursts() * self._burst_info.lines_per_burst * self._raster_info.lines_step
        )

        bursts = []
        for time in azimuth_times:
            if time < bursts_start_times[0] or time > last_time:
                raise CoordinatesOutOfBounds(f"{time} is out of the recorded timeline")

            time_diff = time - bursts_start_times
            time_mask = np.ma.masked_less(time_diff.astype("float64"), 0)
            # associating time only to the first burst containing it
            bursts.append(time_mask.argmin())

        return bursts

    def pixel_to_burst_association(self, azimuth_px_indexes: ArrayLike) -> list[int]:
        """Associate the azimuth pixel value to the right burst. This function returns 1 association for each
        input time.

        Parameters
        ----------
        azimuth_px_indexes : ArrayLike
            azimuth pixel indexes array

        Returns
        -------
        list[int]
            burst associated with a given pixel index

        Raises
        ------
        CoordinatesOutOfBounds
            if input time exceeds tme boundaries of the swath
        """
        if self._burst_info is None:
            return [0] * len(azimuth_px_indexes)

        bursts_lines = np.repeat(self._burst_info.lines_per_burst, self._burst_info.get_number_of_bursts())
        burst_boundaries = np.array([0] + [sum(bursts_lines[: t + 1]) for t, _ in enumerate(bursts_lines)])

        bursts = []
        for coord in azimuth_px_indexes:
            if coord > burst_boundaries[-1]:
                raise CoordinatesOutOfBounds(f"{coord} pixel exceeds swath's bounds")

            px_diff = coord - burst_boundaries
            px_mask = np.ma.masked_less(px_diff, 0)

            bursts.append(px_mask.argmin())

        return bursts

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

        # creating the target block identifier for partial swath reading
        # [start line, start sample, number of lines, number of samples]
        target_block = [
            azimuth_index - np.floor(cropping_size[1] / 2).astype(int),
            range_index - np.floor(cropping_size[0] / 2).astype(int),
            cropping_size[1],
            cropping_size[0],
        ]

        # full raster boundaries and burst boundaries, if applicable
        raster_boundaries = [0, 0, self._raster_layout.lines, self._raster_layout.samples]
        burst_boundaries = None
        # if burst is provided, it means that the ROI to be read must be inside of this burst, otherwise the extracted
        # data are not meaningful with respect to times, acquisition consistency and IRF
        if burst is not None:
            burst_boundaries = [
                self._raster_layout.burst_starting_line_offsets[burst],
                0,
                self._raster_layout.get_burst_lines(burst),
                self._raster_layout.samples,
            ]

        roi_validation(
            roi=target_block,
            raster_boundaries=raster_boundaries,
            burst_boundaries=burst_boundaries,
        )

        data = read_raster_with_raster_info(
            raster_file=self._channel_raster, raster_info=self._raster_info, block_to_read=target_block
        ).T

        # converting to beta nought if radiometric quantity is different
        if self._radiometric_quantity != output_radiometric_quantity:
            azimuth_time, _ = self.pixel_to_times_conversion(azimuth_index=azimuth_index, range_index=range_index)
            incidence_angles = compute_incidence_angles_from_trajectory(
                trajectory=self.trajectory,
                azimuth_time=azimuth_time,
                range_times=self._slant_range_axis[target_block[1] : target_block[1] + target_block[3]],
                look_direction=self.looking_side.value,
            )
            data = radiometric_correction(
                data=data,
                incidence_angle=incidence_angles,
                input_quantity=self._radiometric_quantity,
                output_quantity=output_radiometric_quantity,
            )

        return data
