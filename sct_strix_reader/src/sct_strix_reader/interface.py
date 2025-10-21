# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
StriX format PERSEO-Quality protocol-compliant wrapper
------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from eo_products.strix.utilities import is_strix_product

from sct_strix_reader.protocol_implementation import StriXProductManager


def get_manager() -> type[StriXProductManager]:
    """Retrieve manager"""
    return StriXProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_strix_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
