# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT-Plugin: NovaSAR1 product format reader
------------------------------------------
"""

from sct_novasar1_reader.interface import get_ale_corrector, get_detector, get_manager

__all__ = ["get_manager", "get_detector", "get_ale_corrector"]

__version__ = "1.0.1"
