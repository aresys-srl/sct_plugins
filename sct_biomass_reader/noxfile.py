# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""Automating python testing, formatting and distribution of SCT Biomass Product Plugin"""

import sys

import nox

sys.path.append("..")
import nox_common


@nox.session(python=["3.12", "3.13", "3.14"], venv_backend="conda")
def pytest(session: nox.Session):
    """Execute unittest"""
    session.conda_install("gdal=3.10")
    nox_common.pytest(session)
