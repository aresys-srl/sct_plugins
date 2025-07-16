# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Saocom format Arepyextras-Quality protocol-compliant wrapper
------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.saocom.l1_products.utilities import is_saocom_product

from sct_saocom_reader.protocol_implementation import SAOCOMProductManager


def get_manager() -> type[SAOCOMProductManager]:
    """Retrieve manager"""
    return SAOCOMProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_saocom_product


def get_azimuth_corrections():
    return None


def get_range_corrections():
    return None
