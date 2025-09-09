# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
NovaSAR1 format PERSEO-Quality protocol-compliant wrapper
--------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.novasar.l1_products.utilities import is_novasar_1_product

from sct_novasar1_reader.protocol_implementation import NovaSAR1ProductManager


def get_manager() -> type[NovaSAR1ProductManager]:
    """Retrieve manager"""
    return NovaSAR1ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_novasar_1_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
