# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
EOS-04 format Arepyextras-Quality protocol-compliant wrapper
------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepyextras.eo_products.eos.l1_products.utilities import is_eos04_product

from sct_eos04_reader.protocol_implementation import EOS04ProductManager


def get_manager() -> type[EOS04ProductManager]:
    """Retrieve manager"""
    return EOS04ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_eos04_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
