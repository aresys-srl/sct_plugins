# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""
SCT-Plugin: ENVISAT/ERS product in ASAR format reader
-----------------------------------------------------
"""

from sct_asar_reader.interface import get_ale_corrector, get_detector, get_manager

__all__ = ["get_manager", "get_detector", "get_ale_corrector"]

__version__ = "1.1.0"
