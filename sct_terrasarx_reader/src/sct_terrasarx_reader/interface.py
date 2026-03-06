# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
TERRASAR-X format PERSEO-Quality protocol-compliant wrapper
-----------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_terrasarx_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class TERRASARXProductPlugin:
    """Plugin for TERRASAR-X product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_terrasarx_reader.protocol_implementation import TERRASARXProductManager

        return TERRASARXProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.terrasarx.utilities import is_terrasarx_product

        return is_terrasarx_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
