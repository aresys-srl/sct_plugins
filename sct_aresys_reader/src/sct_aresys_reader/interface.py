# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Aresys product format Arepyextras-Quality protocol-compliant wrapper
--------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from arepytools.io.productfolder2 import is_product_folder as is_aresys_product

from sct_aresys_reader.protocol_implementation import ProductFolderManagerExtended


def get_manager() -> type[ProductFolderManagerExtended]:
    """Retrieve manager"""
    return ProductFolderManagerExtended


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_aresys_product


def get_azimuth_corrections():
    return None


def get_range_corrections():
    return None
