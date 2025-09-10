# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Saocom format PERSEO-Quality protocol-compliant wrapper
------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from eo_products.saocom.utilities import is_saocom_product

from sct_saocom_reader.protocol_implementation import SAOCOMProductManager


def get_manager() -> type[SAOCOMProductManager]:
    """Retrieve manager"""
    return SAOCOMProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_saocom_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
