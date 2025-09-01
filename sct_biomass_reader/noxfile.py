# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""Automating python testing, formatting and distribution of SCT Biomass Product Plugin"""

import sys
from pathlib import Path

import nox

sys.path.append("..")
import nox_common


@nox.session(python=["3.12", "3.13"], venv_backend="conda")
def unittest(session: nox.Session):
    """Execute unittest"""
    session.conda_install("gdal=3.10")
    nox_common.unittest(session)


@nox.session(venv_backend="conda")
def build_doc(session: nox.Session):
    """Build the documentation"""
    session.conda_install("gdal=3.10")
    nox_common.build_doc(session)
