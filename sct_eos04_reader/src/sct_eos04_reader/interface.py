# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
EOS-04 format PERSEO-Quality protocol-compliant wrapper
-------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_eos04_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class EOS04ProductPlugin:
    """Plugin for EOS-04 product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_eos04_reader.protocol_implementation import EOS04ProductManager

        return EOS04ProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.eos04.utilities import is_eos04_product

        return is_eos04_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
