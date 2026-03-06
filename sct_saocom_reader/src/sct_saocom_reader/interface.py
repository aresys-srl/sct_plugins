# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Saocom format PERSEO-Quality protocol-compliant wrapper
-------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_saocom_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class SAOCOMProductPlugin:
    """Plugin for SAOCOM product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_saocom_reader.protocol_implementation import SAOCOMProductManager

        return SAOCOMProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.saocom.utilities import is_saocom_product

        return is_saocom_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
