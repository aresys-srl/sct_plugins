# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Biomass product format PERSEO-Quality protocol-compliant wrapper
---------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bps.transcoder.utils.product_name import is_l1_product_name_valid

from sct_biomass_reader.protocol_implementation import BiomassL1ProductManager

if TYPE_CHECKING:
    from collections.abc import Callable


def is_biomass_product(product: str | Path) -> bool:
    """Detect if the given path is a Biomass product"""

    product_name = Path(product).name
    return is_l1_product_name_valid(product_name)


def get_manager() -> type[BiomassL1ProductManager]:
    """Retrieve manager"""
    return BiomassL1ProductManager


def get_detector() -> Callable[[str | Path], bool]:
    """Retrieve detector"""
    return is_biomass_product


def get_ale_corrector() -> None:
    """Retrieve ALE corrector class"""
    return
