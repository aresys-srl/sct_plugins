# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
COSMO-SkyMed format Arepyextras-Quality protocol-compliant wrapper
------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.cosmo.l1_products.utilities import is_cosmo_product

from sct_cosmo_reader.protocol_implementation import COSMOProductManager


def get_manager() -> type[COSMOProductManager]:
    """Retrieve manager"""
    return COSMOProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_cosmo_product


def get_azimuth_corrections():
    return None


def get_range_corrections():
    return None
