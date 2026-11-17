# SPDX-License-Identifier: MIT

"""Tiny synthetic ICEYE SLC-COG/GRD-COG products (COG .tif + STAC .json) for plugin tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import tifffile
from scipy.constants import speed_of_light

T_REF = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
LINES, SAMPLES = 96, 64
LINE_INTERVAL_US = 100
RANGE_NEAR = 620_000.0
RANGE_SAMPLING_RATE = 300e6
CALIBRATION_FACTOR = 0.05
AMPLITUDE_SCALE = 0.03125
PHASE_SCALE, PHASE_OFFSET = 2 * np.pi / 65535, -np.pi
GRD_SPACING = 0.5
GROUND_TO_SLANT_COEFF = [RANGE_NEAR, 0.62, 2.0e-7, -1.0e-13, 0.0]
INCIDENCE_COEFF = [38.0, 1.5e-3, -2.0e-8, 0.0]


def _iso(time: datetime) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _orbit() -> list[dict]:
    """Earth-fixed state vectors of a 500 km circular orbit around T_REF"""
    a, gm, w_e, inc = 6878137.0, 3.986004418e14, 7.2921150e-5, np.deg2rad(97.4)
    n = np.sqrt(gm / a**3)
    states = []
    for k in range(-30, 31):
        u, th = 0.6 + n * k, w_e * k
        r = a * np.array([np.cos(u), np.sin(u) * np.cos(inc), np.sin(u) * np.sin(inc)])
        v = a * n * np.array([-np.sin(u), np.cos(u) * np.cos(inc), np.cos(u) * np.sin(inc)])
        rot = np.array([[np.cos(th), np.sin(th), 0], [-np.sin(th), np.cos(th), 0], [0, 0, 1]])
        states.append(
            {
                "time": _iso(T_REF + timedelta(seconds=k)),
                "position": (rot @ r).tolist(),
                "velocity": (rot @ (v - np.cross([0, 0, w_e], r))).tolist(),
            }
        )
    return states


def raw_values(level: str) -> np.ndarray:
    """Raw band values (range rows, azimuth columns[, bands]) encoding the pixel position"""
    rows, cols = np.arange(SAMPLES)[:, None], np.arange(LINES)[None, :]
    amplitude = ((rows * 7 + cols * 131) % 60000 + 1).astype(np.uint16)
    if level == "GRD":
        return amplitude
    return np.stack([amplitude, ((rows * 977 + cols * 61) % 65535).astype(np.uint16)], axis=-1)


def expected_samples(level: str, look: str) -> np.ndarray:
    """Decoded samples in legacy (lines, samples) time order, without calibration"""
    raw = raw_values(level)
    columns = np.arange(LINES) if look == "right" else LINES - 1 - np.arange(LINES)
    ordered = np.swapaxes(raw[:, columns], 0, 1)
    if level == "GRD":
        return ordered.astype(np.float32) * np.float32(AMPLITUDE_SCALE)
    amplitude = ordered[..., 0].astype(np.float32) * AMPLITUDE_SCALE
    phase = ordered[..., 1].astype(np.float32) * PHASE_SCALE + PHASE_OFFSET
    return amplitude * np.cos(phase) + 1j * amplitude * np.sin(phase)


def write_cog(folder: Path, level: str = "SLC", look: str = "right") -> tuple[Path, Path]:
    """Write a synthetic ICEYE SLC-COG or GRD-COG product, returns (.tif, .json) paths"""
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"ICEYE_SYNTH_20260101T120000Z_1_X99_SLED_{level}"
    tif_path, json_path = folder / f"{stem}.tif", folder / f"{stem}.json"
    data = raw_values(level)
    bands = [("AMPLITUDE", AMPLITUDE_SCALE, 0.0)] + ([("PHASE", PHASE_SCALE, PHASE_OFFSET)] if level == "SLC" else [])
    gdal = (
        "<GDALMetadata>\n"
        + "\n".join(
            f'  <Item name="NAME" sample="{k}">{n}</Item>\n'
            f'  <Item name="OFFSET" sample="{k}" role="offset">{o!r}</Item>\n'
            f'  <Item name="SCALE" sample="{k}" role="scale">{s!r}</Item>'
            for k, (n, s, o) in enumerate(bands)
        )
        + "\n</GDALMetadata>"
    )
    tifffile.imwrite(
        tif_path,
        data,
        tile=(16, 16),
        photometric="minisblack",
        planarconfig="contig" if data.ndim == 3 else None,
        extratags=[(42112, "s", 0, gdal, True)],
        metadata=None,
    )

    zd_start = T_REF - timedelta(microseconds=LINE_INTERVAL_US * (LINES // 2))
    zd_end = zd_start + timedelta(microseconds=LINE_INTERVAL_US * (LINES - 1))
    properties = {
        "start_datetime": _iso(zd_start),
        "end_datetime": _iso(zd_end),
        "platform": "ICEYE-X99",
        "sat:orbit_state": "ascending",
        "sar:instrument_mode": "spotlight",
        "sar:product_type": f"{level}-COG",
        "sar:polarizations": ["VV"],
        "sar:observation_direction": look,
        "sar:center_frequency": 9.65e9,
        "sar:pixel_spacing_range": round(speed_of_light / (2 * RANGE_SAMPLING_RATE), 6)
        if level == "SLC"
        else GRD_SPACING,
        "iceye:filename": tif_path.name,
        "iceye:orientation": "shadows-down",
        "iceye:zero_doppler_start_datetime": _iso(zd_start),
        "iceye:zero_doppler_end_datetime": _iso(zd_end),
        "iceye:range_near": RANGE_NEAR,
        "iceye:acquisition_range_sampling_rate": RANGE_SAMPLING_RATE,
        "iceye:acquisition_prf": 6000.0,
        "iceye:processing_bandwidth_azimuth": 8000.0,
        "iceye:processing_bandwidth_range": 3.0e8,
        "iceye:pulse_bandwidth": 3.0e8,
        "iceye:pulse_duration": 3.0e-5,
        "iceye:coordinate_frame": "ecef",
        "iceye:orbit_precision": "precise",
        "iceye:orbit_states": _orbit(),
        "iceye:doppler_centroid_coeffs": [[5.0], [15.0]],
        "iceye:doppler_centroid_datetimes": [_iso(zd_start), _iso(zd_end)],
        "iceye:incidence_angle_coeffs": INCIDENCE_COEFF,
        "iceye:ground_to_slant_coeff": GROUND_TO_SLANT_COEFF,
        "iceye:calibration_factor": CALIBRATION_FACTOR,
        "iceye:amplitude_mapping": {"function": "minmax", "parameters": {"scale": 1, "exponent": 1}},
    }
    item = {
        "type": "Feature",
        "id": stem,
        "bbox": [12.0, 45.0, 12.1, 45.1],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[12.0, 45.0], [12.1, 45.0], [12.1, 45.1], [12.0, 45.1], [12.0, 45.0]]],
        },
        "properties": properties,
        "assets": {"data": {"href": tif_path.name, "type": "image/tiff; application=geotiff", "roles": ["data"]}},
    }
    json_path.write_text(json.dumps(item))
    return tif_path, json_path
