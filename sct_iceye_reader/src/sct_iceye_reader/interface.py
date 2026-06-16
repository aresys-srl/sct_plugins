# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""ICEYE SCT plugin interface."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from sct_iceye_reader import __version__

if TYPE_CHECKING:
    from sct.io.extended_protocols import ALECorrectionFunctionType, SCTInputProduct


class ICEYEProductPlugin:
    """Plugin for ICEYE product format"""

    version = __version__

    @classmethod
    def get_manager(cls) -> type[SCTInputProduct]:
        from sct_iceye_reader.protocol_implementation import ICEYEProductManager

        return ICEYEProductManager

    @classmethod
    def get_detector(cls) -> Callable[[str | Path], bool]:
        from eo_products.iceye.utilities import is_iceye_product

        return is_iceye_product

    @classmethod
    def get_ale_corrector(cls) -> ALECorrectionFunctionType:
        return None
