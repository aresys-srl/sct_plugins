# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Loading ETAD corrections
------------------------
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd
from s1etad import ECorrectionType, Sentinel1Etad, Sentinel1EtadBurst
from scipy.interpolate import RegularGridInterpolator
from shapely.errors import ShapelyDeprecationWarning
from shapely.geometry import Point

from sct_sentinel1_reader.corrections import ALE_CORRECTIONS_FIELDS

# due to s1etad use of deprecated shapely function
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)


def _extract_etad_correction(burst: Sentinel1EtadBurst, location: Point) -> tuple[float, float]:
    """Extracting ALE range correction from ETAD product for a given point target location.

    Parameters
    ----------
    burst : Sentinel1EtadBurst
        burst where the target lies
    location : Point
        location of the target

    Returns
    -------
    float
        range ALE correction in meters
    float
        azimuth ALE correction in meters
    """
    # get SAR times at which it is seen in the scene
    tau0, t0 = burst.geodetic_to_radar(location.y, location.x, location.z)
    # retrieving sum of all corrections along range direction
    correction = burst.get_correction(ECorrectionType.SUM, meter=True)
    rng_corrections = correction["x"]
    az_corrections = correction["y"]

    # interpolating values at given target time coordinates
    azimuth_time, range_time = burst.get_burst_grid()
    interpolator_rng = RegularGridInterpolator(
        points=(azimuth_time, range_time), method="linear", values=rng_corrections, fill_value=0, bounds_error=False
    )
    interpolator_az = RegularGridInterpolator(
        points=(azimuth_time, range_time), method="linear", values=az_corrections, fill_value=0, bounds_error=False
    )

    return interpolator_rng((t0, tau0))[0], interpolator_az((t0, tau0))[0]


def get_etad_corrections(etad_product_path: Path, data: pd.DataFrame) -> pd.DataFrame:
    """Retrieving range ALE correction from ETAD product for all point targets.

    Parameters
    ----------
    etad_product_path : Path
        path to the ETAD product
    data : pd.DataFrame
        point targets results dataframe

    Returns
    -------
    pd.DataFrame
        corrections dataframe
    """

    # opening ETAD product
    etad = Sentinel1Etad(etad_product_path)

    corrections = []
    for _, row in data.iterrows():
        # creating a Point instance for the current cor
        cr_point = Point(row["longitude_deg"], row["latitude_deg"], row["altitude_m"])
        cr_burst_location = etad.query_burst(geometry=cr_point)
        if cr_burst_location.empty:
            continue

        total_rng_correction, total_az_correction = _extract_etad_correction(
            burst=next(etad.iter_bursts(cr_burst_location)), location=cr_point
        )

        corrections.append(
            {
                "target_name": row["target_name"],
                ALE_CORRECTIONS_FIELDS["etad_range"]: total_rng_correction,
                ALE_CORRECTIONS_FIELDS["etad_azimuth"]: total_az_correction,
            }
        )
    corrections_df = pd.DataFrame(corrections)

    return pd.concat([data.copy(), corrections_df.drop("target_name", axis=1)], axis=1)
