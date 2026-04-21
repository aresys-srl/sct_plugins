# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Biomass product format PERSEO-Quality protocol-compliant wrapper
----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_biomass_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class BIOMASSProductPlugin:
    """Plugin for BIOMASS product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_biomass_reader.protocol_implementation import BiomassL1ProductManager

        return BiomassL1ProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from bps.transcoder.utils.product_name import is_l1_product_name_valid

        def _is_valid_biomass_product(product_path: str | Path) -> bool:
            return is_l1_product_name_valid(Path(product_path).name)

        return _is_valid_biomass_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
