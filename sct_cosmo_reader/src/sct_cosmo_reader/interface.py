# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
COSMO-SkyMed format PERSEO-Quality protocol-compliant wrapper
-------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_cosmo_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class COSMOProductPlugin:
    """Plugin for COSMO product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_cosmo_reader.protocol_implementation import COSMOProductManager

        return COSMOProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.cosmo.utilities import is_cosmo_product

        return is_cosmo_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
