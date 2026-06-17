# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""Common Enum, dataclasses and other utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal

import numpy as np
from numpy.polynomial import Polynomial
from perseo_core.timing import PreciseDateTime
from scipy.interpolate import CubicSpline

LookingDirection = Literal["LEFT", "RIGHT"]


class SARRadiometricQuantity(Enum):
    """Enum class for radiometric analysis input/output quantity types"""

    BETA_NOUGHT = auto()
    SIGMA_NOUGHT = auto()
    GAMMA_NOUGHT = auto()


class SARPolarization(Enum):
    """Polarization enum class"""

    HH = "H/H"
    VV = "V/V"
    HV = "H/V"
    VH = "V/H"


class SARProjection(Enum):
    """Enum class for managing swath projection of product folder"""

    SLANT_RANGE = "SLANT RANGE"
    GROUND_RANGE = "GROUND RANGE"


class OrbitDirection(Enum):
    """Orbit direction: ascending or descending"""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class StandardSARAcquisitionMode(Enum):
    """Standard cross-package SAR acquisition mode definition"""

    SCANSAR = auto()
    SPOTLIGHT = auto()
    STRIPMAP = auto()
    TOPSAR = auto()
    WAVE = auto()
    UNKNOWN = auto()


@dataclass
class PulseInfo:
    """Chirp pulse info"""

    length_s: float
    bandwidth_hz: float
    sampling_rate_hz: float
    energy_j: float
    start_frequency_hz: float
    start_phase: float
    direction: str


@dataclass
class DatasetInfo:
    """Dataset Info"""

    fc_hz: float
    acquisition_mode: str
    sensor_name: str
    image_type: str
    projection: str
    side_looking: LookingDirection


@dataclass
class RasterInfo:
    """Product Raster Info"""

    lines: RasterInfoAxis
    samples: RasterInfoAxis
    data_type: str | None = None
    raster_name: str | None = None


@dataclass
class RasterInfoAxis:
    """Axis representation for RasterInfo"""

    length: int
    step: float
    start: float | PreciseDateTime
    step_unit: str
    axis: np.ndarray = field(init=False)

    def __post_init__(self):
        # generating axis array from inputs
        self.axis = np.arange(0, self.length, 1) * self.step + self.start


@dataclass
class SARSamplingFrequencies:
    """SAR signal sampling frequencies"""

    range_freq_hz: float
    range_bandwidth_freq_hz: float
    azimuth_freq_hz: float
    azimuth_bandwidth_freq_hz: float


@dataclass
class ConversionFunction:
    """Generic conversion function wrapper"""

    azimuth_reference_time: PreciseDateTime
    origin: float
    function: Polynomial | CubicSpline


@dataclass
class ConversionPolynomial:
    """Generic conversion polynomial wrapper"""

    azimuth_reference_time: PreciseDateTime
    origin: float
    polynomial: Polynomial | CubicSpline


@dataclass
class DopplerEvaluator:
    """Doppler function (rate/centroid) evaluator"""

    functions: list[ConversionFunction] | None = None
    azimuth_reference_times: np.ndarray | None = None

    def evaluate(self, azimuth_time: PreciseDateTime, slant_range: np.ndarray) -> np.ndarray:
        """Evaluate function at given inputs.

        Parameters
        ----------
        azimuth_time : PreciseDateTime
            azimuth time to select the proper function
        slant_range : np.ndarray
            slant range value(s) in meters

        Returns
        -------
        np.ndarray
            Doppler functions values at slant range
        """
        poly_index = detect_right_polynomial_index(
            azimuth_time=azimuth_time, reference_azimuth_times=self.azimuth_reference_times
        )
        poly = self.functions[poly_index]
        return poly.function(slant_range - poly.origin)


def detect_right_polynomial_index(azimuth_time: PreciseDateTime, reference_azimuth_times: np.ndarray) -> int:
    """Detecting the index of the right polynomial to be used given an input azimuth time.
    The polynomial to be used is the one with reference azimuth time closest to the input value but with
    reference_azimuth_time < input_azimuth_time.

    Parameters
    ----------
    azimuth_time : PreciseDateTime
        selected azimuth time
    reference_azimuth_times : np.ndarray
        array of reference azimuth times, in PreciseDateTime format

    Returns
    -------
    int
        index corresponding to the polynomial to be used
    """
    diff = np.array(azimuth_time - reference_azimuth_times).astype("float")
    return np.ma.masked_where(diff < 0, diff).argmin()
