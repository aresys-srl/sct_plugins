# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""Automating python testing, formatting and distribution of SCT ENVISAT/ERS in ASAR format Plugin"""

import sys
from pathlib import Path
import glob
import nox

sys.path.append("..")
import nox_common

_LICENSE_HEADER_GPL = """# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: GPLv3+

"""

@nox.session()
def check_format(session: nox.Session):
    """Check proper formatting with ruff. Check presence of license header"""
    session.install("ruff")
    session.run("ruff", "--version")
    session.run("ruff", "format", "--check")
    session.run("ruff", "check")

    def wrong_license_header(file: str) -> bool:
        with open(file, "r", encoding="utf-8") as ifile:
            first_line = ifile.readline()
            if "# noqa:" in first_line:
                first_line = ifile.readline()
            header = first_line + ifile.readline() + ifile.readline()
            validation = header != _LICENSE_HEADER_GPL
            return validation

    source_files = glob.glob("src/**/*.py", recursive=True)
    no_licensed_files = list(filter(wrong_license_header, source_files))

    if len(no_licensed_files) > 0:
        for file in no_licensed_files:
            session.warn(f"{file} has no license header")
        session.error()
