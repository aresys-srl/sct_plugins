# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Sentinel-1 format PERSEO-Quality protocol-compliant wrapper
----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from eo_products.sentinel1.utilities import is_s1_safe_product

from sct_sentinel1_reader.corrections.main import S1ALECorrector
from sct_sentinel1_reader.protocol_implementation import Sentinel1ProductManager


def get_manager() -> type[Sentinel1ProductManager]:
    """Retrieve manager"""
    return Sentinel1ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_s1_safe_product


def get_ale_corrector() -> type[S1ALECorrector]:
    """Retrieve ALE corrector class"""
    return S1ALECorrector
