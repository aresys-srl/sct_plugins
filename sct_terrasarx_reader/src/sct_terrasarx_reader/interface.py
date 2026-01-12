# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
TERRASAR-X format PERSEO-Quality protocol-compliant wrapper
-----------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from eo_products.terrasarx.utilities import is_terrasarx_product

from sct_terrasarx_reader.protocol_implementation import TERRASARXProductManager


def get_manager() -> type[TERRASARXProductManager]:
    """Retrieve manager"""
    return TERRASARXProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_terrasarx_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
