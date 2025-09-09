# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
ICEYE format PERSEO-Quality protocol-compliant wrapper
-----------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.iceye.l1_products.utilities import is_iceye_product

from sct_iceye_reader.protocol_implementation import ICEYEProductManager


def get_manager() -> type[ICEYEProductManager]:
    """Retrieve manager"""
    return ICEYEProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_iceye_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
