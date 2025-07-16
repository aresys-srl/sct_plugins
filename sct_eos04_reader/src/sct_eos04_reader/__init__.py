# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT-Plugin: EOS-04 product format reader
----------------------------------------
"""

from sct_eos04_reader.interface import get_azimuth_corrections, get_detector, get_manager, get_range_corrections

__all__ = ["get_manager", "get_detector", "get_azimuth_corrections", "get_range_corrections"]

__version__ = "1.0.0"
