# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Sentinel-1 IPF range and azimuth custom corrections
---------------------------------------------------
"""

from uuid import uuid4

import numpy as np
import pandas as pd
from arepytools.timing.precisedatetime import PreciseDateTime
from eo_products.sentinel1.utilities import S1AcquisitionMode
from numpy.typing import ArrayLike
from perseo_quality.io.quality_input_protocol import QualityInputProduct
from scipy.constants import speed_of_light
from sct.configuration.logger import sct_logger
from sct.io.extended_protocols import SCTInputProduct


def compute_doppler_shift_correction(pulse_rate: ArrayLike, squint_frequency: ArrayLike) -> ArrayLike:
    """Compute doppler shift correction that affects ALE along range direction.

    The term doppler_shift_correction should be added to the coordinate found by measurement
    The negative sign is added so that the function returns a value that can be subtracted from the coordinate found by
    measurement.

    Parameters
    ----------
    pulse_rate : ArrayLike
        signal pulse rate as signal bandwidth divided by pulse length, float or array
    squint_frequency : ArrayLike
        squint frequency in Hz, float or array

    Returns
    -------
    ArrayLike
        doppler shift correction in meters
    """

    # compute range corrections: doppler shift correction
    doppler_shift = squint_frequency / pulse_rate
    doppler_shift_correction = doppler_shift * speed_of_light / 2

    return -doppler_shift_correction


def compute_fmrate_shift_correction(
    ground_velocity: float,
    doppler_frequency: float,
    doppler_rate_processor: np.ndarray,
    doppler_rate_geometry: np.ndarray,
) -> float:
    """Compute FM rate shift correction.

    The term fmrate_shift should be subtracted from the coordinate found by measurement

    Parameters
    ----------
    ground_velocity : float
        sensor ground velocity
    doppler_frequency : float
        doppler frequency in Hz
    doppler_rate_processor : np.ndarray
        doppler rate applied by the SAR processor
    doppler_rate_geometry : np.ndarray
        doppler rate derived from the orbit to ground point geometry

    Returns
    -------
    float
        FM rate shift correction in meters
    """

    fmrate_shift = doppler_frequency * (-1 / doppler_rate_processor + 1 / doppler_rate_geometry)
    return fmrate_shift * ground_velocity


def compute_instrument_timing_correction(
    ground_velocity: float, azimuth_time: PreciseDateTime, swst_changes: list, pulse_latch_time: float
) -> float:
    """Compute instrument timing correction.

    Parameters
    ----------
    ground_velocity : float
        sensor ground velocity
    azimuth_time : PreciseDateTime
        azimuth time when to compute the timing correction
    swst_changes : list
        swst changes list
    pulse_latch_time : float
        tx pulse latch time

    Returns
    -------
    float
        instrument timing correction in meters
    """
    swst_times = np.array([t[0] for t in swst_changes])
    swst_values = [t[1] for t in swst_changes]
    # taking the change time that is closest to the input azimuth time and that is before that time
    selected_change_time_idx = np.ma.masked_less(np.abs(azimuth_time - swst_times).astype(float), 0).argmin()

    instrument_timing = swst_values[selected_change_time_idx] + pulse_latch_time
    return -instrument_timing * ground_velocity


def compute_mid_swath_index(acquisition_mode: S1AcquisitionMode) -> int:
    """Compute mid-swath index from acquisition mode.

    Parameters
    ----------
    acquisition_mode : S1AcquisitionMode
        sensor acquisition mode

    Returns
    -------
    int
        mid-swath index
    """
    if acquisition_mode == S1AcquisitionMode.IW:
        return 1
    if acquisition_mode == S1AcquisitionMode.EW:
        return 2
    if acquisition_mode in (S1AcquisitionMode.SM, S1AcquisitionMode.WV):
        # for SM and WV the mid-swath index is the current swath
        return -1


def compute_real_bistatic_delay_correction(
    ground_velocity: float, range_time: float, bistatic_delay_applied: float, burst_start_time: float
) -> float:
    """Compute the correct bistatic delay for the current point.
    Processor computed bistatic delay (bistatic_delay_applied) is removed and the properly evaluated delay is then
    added. Delay is computed as:

    .. math::

        \\frac{\\tau_0 - \\Delta \\tau}{2}

    The term bistatic_delay should be added to the coordinate found by measurement
    The negative sign is added so that the function returns a value that can be subtracted from the coordinate found by
    measurement.


    Parameters
    ----------
    ground_velocity : float
        ground velocity
    range_time : float
        range time of the point of interest
    bistatic_delay_applied : float
        bistatic delay already applied by the processor, to be removed and substituted with correct one
    burst_start_time : float
        start time of the burst where the point of interest belongs to

    Returns
    -------
    float
        bistatic delay correction in meters
    """
    delta_tau = range_time - burst_start_time
    bistatic_delay = bistatic_delay_applied + (-burst_start_time + delta_tau) / 2
    return -bistatic_delay * ground_velocity


def _detect_mid_swath_channel(subswaths: list[str]) -> str:
    """Detecting the mid swath channel name. For Sentinel-1, only IW and EW
    acquisition modes have multiple sub-swaths. For them, the middle sub-swaths
    are IW2 and EW3, respectively. All other modes have a single swath.

    Parameters
    ----------
    times : list[str]
        list with values being the sub-swath names

    Returns
    -------
    str
        mid-swath name
    """
    swath_names = sorted(subswaths)
    if swath_names == ["IW1", "IW2", "IW3"]:
        return "IW2"
    if swath_names == ["EW1", "EW2", "EW3", "EW4", "EW5"]:
        return "EW3"
    assert len(swath_names) == 1
    return swath_names[0]


def _get_rid_of_pol_dependency(arg: dict[str, dict[str, tuple[PreciseDateTime, float]]]) -> dict[str, PreciseDateTime]:
    """Removing polarization dependency from the input dictionary by selecting only the minimum start time.

    Parameters
    ----------
    arg : dict[str, dict[str, tuple[PreciseDateTime, float]]]
        dictionary with keys being the swath id and values being dictionaries of polarizations as keys and azimuth
        and range mid burst times as values

    Returns
    -------
    dict[str, PreciseDateTime]
        dictionary of swath id as keys and azimuth start times as values, one value for each key
    """
    arg = arg.copy()
    for key, val in arg.items():
        vals = list(val.values())
        arg[key] = vals[np.argmin([v[0] for v in val.values()])]

    return arg


def compute_range_corrections(
    product: QualityInputProduct,
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Computing Sentinel-1 specific range corrections for ALE measurements.
    In this case, the only range correction is Doppler Shift.

    Parameters
    ----------
    product : QualityInputProduct
        product
    data : pd.DataFrame
        point target analysis data

    Returns
    -------
    pd.DataFrame
        dataframe with doppler shift range correction
    """
    # retrieving pulse rates for each channel
    pulse_rates = dict.fromkeys(product.channels_list)
    for ch_id in product.channels_list:
        channel_data = product.get_channel_data(channel_id=ch_id)
        pulse_rates[ch_id] = channel_data.pulse_rate

    # computing range corrections
    rng_corr = []
    for _, row in data.iterrows():
        rng_corr.append(
            (
                row["id"],
                compute_doppler_shift_correction(
                    pulse_rate=pulse_rates[row["channel"]], squint_frequency=row["total_doppler_frequency_[Hz]"]
                ),
            )
        )

    return pd.DataFrame(rng_corr, columns=["id", "doppler_shift_range_correction_[m]"])


def compute_azimuth_corrections(
    product: QualityInputProduct,
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Computing Sentinel-1 specific azimuth corrections for ALE measurements.
    FM rate shift, instrument timing and bistatic delay corrections are computed.

    Parameters
    ----------
    product : QualityInputProduct
        product
    data : pd.DataFrame
        point target analysis data

    Returns
    -------
    pd.DataFrame
        dataframe with fm rate shift, instrument timing and bistatic delay correction
    """

    swst_changes = dict.fromkeys(product.channels_list)
    pulse_latch_times = swst_changes.copy()
    subswath_mid_first_burst_times = {}
    burst_start_times = swst_changes.copy()

    # retrieving swst changes for each channel and detecting the mid swath for the current product
    for ch_id in product.channels_list:
        channel_data = product.get_channel_data(channel_id=ch_id)
        swst_changes[ch_id] = channel_data.swst_changes
        pulse_latch_times[ch_id] = channel_data.pulse_latch_time
        if channel_data._channel.burst_info.num > 0:
            burst_start_times[ch_id] = channel_data._channel.burst_info.range_start_times
        else:
            burst_start_times[ch_id] = channel_data._channel.raster_info.samples.start
        if channel_data.swath_name not in subswath_mid_first_burst_times:
            subswath_mid_first_burst_times[channel_data.swath_name] = {}
        if channel_data.polarization.value not in subswath_mid_first_burst_times[channel_data.swath_name]:
            subswath_mid_first_burst_times[channel_data.swath_name][channel_data.polarization.value] = (
                channel_data.get_mid_burst_times(0)
            )

    subswath_mid_first_burst_times = _get_rid_of_pol_dependency(subswath_mid_first_burst_times)
    mid_swath_channel_id = _detect_mid_swath_channel(subswaths=list(subswath_mid_first_burst_times.keys()))
    bistatic_delay_applied = subswath_mid_first_burst_times[mid_swath_channel_id][1] / 2

    # computing azimuth corrections
    fm_rate_shift = []
    instrument_timing = []
    bistatic_delay = []
    for _, row in data.iterrows():
        try:
            fm_rate_shift.append(
                (
                    row["id"],
                    compute_fmrate_shift_correction(
                        ground_velocity=row["ground_velocity_[ms]"],
                        doppler_frequency=row["total_doppler_frequency_[Hz]"],
                        doppler_rate_processor=row["doppler_rate_real_[Hzs]"],
                        doppler_rate_geometry=row["doppler_rate_theoretical_[Hzs]"],
                    ),
                )
            )

        except (ValueError, TypeError):
            fm_rate_shift.append((row["id"], np.nan))

        try:
            instrument_timing.append(
                (
                    row["id"],
                    compute_instrument_timing_correction(
                        ground_velocity=row["ground_velocity_[ms]"],
                        azimuth_time=row["peak_azimuth_time_[UTC]"],
                        pulse_latch_time=pulse_latch_times[row["channel"]],
                        swst_changes=swst_changes[row["channel"]],
                    ),
                )
            )

        except (ValueError, TypeError):
            instrument_timing.append((row["id"], np.nan))

        try:
            bistatic_delay.append(
                (
                    row["id"],
                    compute_real_bistatic_delay_correction(
                        ground_velocity=row["ground_velocity_[ms]"],
                        range_time=row["peak_range_time_[s]"],
                        bistatic_delay_applied=bistatic_delay_applied,
                        burst_start_time=burst_start_times[row["channel"]][row["burst"]],
                    ),
                )
            )

        except (ValueError, TypeError):
            bistatic_delay.append((row["id"], np.nan))

    # converting output to dataframe
    fm_rate_shift = pd.DataFrame(fm_rate_shift, columns=["id", "fm_rate_shift_azimuth_correction_[m]"])
    instrument_timing = pd.DataFrame(instrument_timing, columns=["id", "instrument_timing_azimuth_correction_[m]"])
    bistatic_delay = pd.DataFrame(bistatic_delay, columns=["id", "bistatic_delay_azimuth_correction_[m]"])
    az_corrections = fm_rate_shift.merge(instrument_timing, on="id").merge(bistatic_delay, on="id")

    return az_corrections


def compute_corrections(product: SCTInputProduct, data: pd.DataFrame) -> pd.DataFrame:
    """Computing Sentinel-1 IPF custom Absolute Localization Error corrections.

    Parameters
    ----------
    product : SCTInputProduct
        Sentinel-1 product
    data : pd.DataFrame
        point target analysis results dataframe

    Returns
    -------
    pd.DataFrame
        updated dataframe with sensor specific ALE corrections
    """
    data_ = data.copy()
    data_["id"] = [uuid4() for _ in range(len(data_))]
    sct_logger.info("Computing sensor specific range corrections...")
    range_corrections_df = compute_range_corrections(product, data_.copy())

    sct_logger.info("Computing sensor specific azimuth corrections...")
    azimuth_corrections_df = compute_azimuth_corrections(product, data_.copy())

    data_out = data_.merge(range_corrections_df, on="id").merge(azimuth_corrections_df, on="id")
    data_out.drop(columns="id", axis=1, inplace=True)

    return data_out
