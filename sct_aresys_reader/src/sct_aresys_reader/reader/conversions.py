# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Coordinate conversions module
-----------------------------
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Union

import numpy as np


@dataclass(frozen=True)
class Ellipsoid:
    """
    Ellipsoid class.

    Examples
    --------
    >>> ellipsoid = Ellipsoid(1.0, 3.0)
    >>> ellipsoid = Ellipsoid(3.0, 1.0)

    See also
    --------
    WGS84 : common earth ellispoid
    """

    semi_major_axis: float = field(init=False)
    semi_minor_axis: float = field(init=False)
    semi_axes_ratio_min_max: float = field(init=False)
    eccentricity_square: float = field(init=False)
    eccentricity: float = field(init=False)
    ep2: float = field(init=False)

    first_semi_axis: InitVar[float]
    second_semi_axis: InitVar[float]

    def __post_init__(self, first_semi_axis, second_semi_axis):
        """Initialize the object with the specified ellipsoid parameters

        Parameters
        ----------
        first_semi_axis : float
            length of the first semi-axis of the ellipsoid
        second_semi_axis : float
            length of the second semi-axis of the ellipsoid

        Raises
        ------
        ValueError
            in case of negative input axis
        """
        if first_semi_axis <= 0 or second_semi_axis <= 0:
            raise ValueError("Non-positive input axes")

        object.__setattr__(self, "semi_major_axis", max(first_semi_axis, second_semi_axis))
        object.__setattr__(self, "semi_minor_axis", min(first_semi_axis, second_semi_axis))
        object.__setattr__(self, "semi_axes_ratio_min_max", self.semi_minor_axis / self.semi_major_axis)
        object.__setattr__(self, "eccentricity_square", 1 - self.semi_axes_ratio_min_max**2)
        object.__setattr__(self, "eccentricity", np.sqrt(self.eccentricity_square))
        object.__setattr__(self, "ep2", 1.0 / self.semi_axes_ratio_min_max**2 - 1)

    def inflate(self, height: float) -> Ellipsoid:
        """Compute an ellipsoid by adding height to the semi-axis

        Parameters
        ----------
        height : float
            additional height, it can be negative

        Examples
        --------
        >>> a = Ellipsoid(1.0, 3.0)
        >>> b = a.inflate(2)
        >>> print(b)
        Ellipsoid(semi_major_axis=5.0, semi_minor_axis=3.0,
                  semi_axes_ratio_min_max=0.6, eccentricity_square=0.64,
                  eccentricity=0.8, ep2=1.7777777777777777)
        """
        return Ellipsoid(self.semi_major_axis + height, self.semi_minor_axis + height)


_A_MAX = 6.378137e6  # semi-major axis
_A_MIN = 6.356752314245e6  # semi-minor axis

WGS84 = Ellipsoid(_A_MAX, _A_MIN)

_NUMBER_OF_ITERATIONS = 5

_A_MAX_SQUARE_MINUS_A_MIN_SQUARE_DIVIDED_BY_A_MAX = (
    WGS84.semi_major_axis**2 - WGS84.semi_minor_axis**2
) / WGS84.semi_major_axis
_A_MIN_TIMES_EP2 = WGS84.semi_minor_axis * WGS84.ep2


def llh2xyz(coordinates: Union[list, np.ndarray]) -> np.ndarray:
    """Conversion from llh geodetic coordinates to xyz

    Parameters
    ----------
    coordinates : Union[list, np.ndarray]
        a numpy ndarray of shape (3,), (3, 1) or (3, N) or a list

    Returns
    -------
    np.ndarray
        a two dimensional numpy array of shape (3, N) with xyz coordinates
    """
    coordinates = np.asarray(coordinates)
    if coordinates.shape[0] != 3:
        raise RuntimeError(f"Coordinates has wrong shape: {coordinates.shape} not in (3,), (3, 1) or (3, N)")

    if coordinates.ndim == 1:
        coordinates = coordinates.copy()
        coordinates.shape = (3, 1)

    lat = coordinates[0, :]
    lon = coordinates[1, :]
    h = coordinates[2, :]

    big_n = WGS84.semi_major_axis / np.sqrt(1 - WGS84.eccentricity_square * np.sin(lat) ** 2)
    r = (big_n + h) * np.cos(lat)

    x = r * np.cos(lon)
    y = r * np.sin(lon)
    z = (big_n * WGS84.semi_axes_ratio_min_max**2 + h) * np.sin(lat)

    return np.vstack((x, y, z)).astype(float)


def xyz2llh(coordinates: Union[list, np.ndarray]) -> np.ndarray:
    """Conversion from xyz coordinates to llh geodetic coordinates

    Parameters
    ----------
    coordinates : Union[list, np.ndarray]
        a numpy ndarray of shape (3,), (3, 1) or (3, N) or a list

    Returns
    -------
    np.ndarray
        a two dimensional numpy array of shape (3, N) with llh coordinates
    """
    coordinates = np.asarray(coordinates)
    if coordinates.shape[0] != 3:
        raise RuntimeError(f"Coordinates has wrong shape: {coordinates.shape} not in (3,), (3, 1) or (3, N)")

    if coordinates.ndim == 1:
        coordinates = coordinates.copy()
        coordinates.shape = (3, 1)

    x = coordinates[0, :]
    y = coordinates[1, :]
    z = coordinates[2, :]

    lon = np.arctan2(y, x)

    k = np.maximum(np.absolute(x), np.absolute(y))
    k[np.where(k == 0)] = 1.0

    c1 = x / k
    c2 = y / k

    r = k * np.sqrt(c1**2 + c2**2)

    beta = np.arctan2(z, r * WGS84.semi_axes_ratio_min_max)
    sin_beta, cos_beta = np.sin(beta), np.cos(beta)

    lat = np.arctan2(
        z + _A_MIN_TIMES_EP2 * sin_beta**3,
        r - _A_MAX_SQUARE_MINUS_A_MIN_SQUARE_DIVIDED_BY_A_MAX * cos_beta**3,
    )
    beta_new = np.arctan2(WGS84.semi_axes_ratio_min_max * np.sin(lat), np.cos(lat))

    for _ in range(_NUMBER_OF_ITERATIONS):
        if np.array_equal(beta, beta_new):
            break

        beta = beta_new
        sin_beta, cos_beta = np.sin(beta), np.cos(beta)

        lat = np.arctan2(
            z + _A_MIN_TIMES_EP2 * sin_beta**3,
            r - _A_MAX_SQUARE_MINUS_A_MIN_SQUARE_DIVIDED_BY_A_MAX * cos_beta**3,
        )
        beta_new = np.arctan2(WGS84.semi_axes_ratio_min_max * np.sin(lat), np.cos(lat))

    # Compute height
    sin_phi = np.sin(lat)
    big_n = WGS84.semi_major_axis / np.sqrt(1 - sin_phi**2 * WGS84.eccentricity_square)
    h = r * np.cos(lat) + (z + WGS84.eccentricity_square * big_n * sin_phi) * sin_phi - big_n

    return np.vstack((lat, lon, h)).astype(float)
