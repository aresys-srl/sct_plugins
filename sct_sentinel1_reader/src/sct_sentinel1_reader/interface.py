# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Sentinel-1 format Arepyextras-Quality protocol-compliant wrapper
----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.safe.l1_products.utilities import is_s1_safe_product

from sct_sentinel1_reader.custom_corrections import compute_azimuth_corrections, compute_range_corrections
from sct_sentinel1_reader.protocol_implementation import Sentinel1ProductManager


def get_manager() -> type[Sentinel1ProductManager]:
    """Retrieve manager"""
    return Sentinel1ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_s1_safe_product


def get_azimuth_corrections():
    return compute_azimuth_corrections


def get_range_corrections():
    return compute_range_corrections
