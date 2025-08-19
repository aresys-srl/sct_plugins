# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""
ENVISAT/ERS ASAR format Arepyextras-Quality protocol-compliant wrapper
----------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from sct_asar_reader.core.utilities import is_asar_product
from sct_asar_reader.protocol_implementation import ASARProductManager


def get_manager() -> type[ASARProductManager]:
    """Retrieve manager"""
    return ASARProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_asar_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return None
