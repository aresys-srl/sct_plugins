# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Sentinel-1 format PERSEO-Quality protocol-compliant wrapper
----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_sentinel1_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class Sentinel1InputProductPlugin:
    """Plugin for Sentinel-1 product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        """Implementation of Plugin interface method to get the Product Manager class"""
        from sct_sentinel1_reader.protocol_implementation import Sentinel1ProductManager

        return Sentinel1ProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        """Implementation of Plugin interface method to get the product detection function"""
        from eo_products.sentinel1.utilities import is_s1_safe_product

        return is_s1_safe_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        """Implementation of Plugin interface method to get the Absolute Localization Error Correction class"""
        from sct_sentinel1_reader.corrections.main import S1ALECorrector

        return S1ALECorrector
