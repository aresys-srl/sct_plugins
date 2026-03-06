# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""
ENVISAT/ERS ASAR format PERSEO-Quality protocol-compliant wrapper
-----------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_asar_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class ASARProductPlugin:
    """Plugin for ASAR product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_asar_reader.protocol_implementation import ASARProductManager

        return ASARProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from sct_asar_reader.core.utilities import is_asar_product

        return is_asar_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
