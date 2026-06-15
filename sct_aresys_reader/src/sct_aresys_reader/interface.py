# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Aresys product format PERSEO-Quality protocol-compliant wrapper
--------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_aresys_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class AresysInputProductPlugin:
    """Plugin for Aresys product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_aresys_reader.protocol_implementation import ProductFolderManagerExtended

        return ProductFolderManagerExtended

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from sct_aresys_reader.reader.io.productfolder2 import is_product_folder as is_aresys_product

        return is_aresys_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
