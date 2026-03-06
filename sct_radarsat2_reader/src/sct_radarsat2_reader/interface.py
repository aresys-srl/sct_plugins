# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
RADARSAT-2 format PERSEO-Quality protocol-compliant wrapper
-----------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_radarsat2_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class RADARSAT2ProductPlugin:
    """Plugin for RADARSAT-2 product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_radarsat2_reader.protocol_implementation import RADARSAT2ProductManager

        return RADARSAT2ProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.radarsat2.utilities import is_radarsat_product

        return is_radarsat_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
