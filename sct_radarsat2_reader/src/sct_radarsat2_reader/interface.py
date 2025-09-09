# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
RADARSAT-2 format PERSEO-Quality protocol-compliant wrapper
----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.radarsat.l1_products.utilities import is_radarsat_product

from sct_radarsat2_reader.protocol_implementation import RADARSAT2ProductManager


def get_manager() -> type[RADARSAT2ProductManager]:
    """Retrieve manager"""
    return RADARSAT2ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_radarsat_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
