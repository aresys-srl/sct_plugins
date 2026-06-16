# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""NovaSAR-1 SCT plugin interface."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_novasar1_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class NovaSAR1InputProductPlugin:
    """Plugin for NovaSAR-1 product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_novasar1_reader.protocol_implementation import NovaSAR1ProductManager

        return NovaSAR1ProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.novasar1.utilities import is_novasar_1_product

        return is_novasar_1_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
