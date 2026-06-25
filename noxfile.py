# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""Automating SCT Plugins documentation NOX sessions"""

import os
import shutil
from datetime import datetime
from pathlib import Path

import nox


@nox.session()
def build_doc(session: nox.Session):
    """Building documentation"""

    if Path("site").exists():
        shutil.rmtree("site")

    tag = os.getenv("CI_COMMIT_TAG") or os.getenv("GITHUB_REF_NAME", "dev")
    sha = os.getenv("CI_COMMIT_SHORT_SHA")
    date = datetime.now().strftime("%Y-%m-%d")

    if sha is None:
        try:
            sha = session.run(
                "git", "rev-parse", "--short", "HEAD", external=True, silent=True
            ).strip()
        except Exception:
            sha = ""

    doc_name = f"{date}-{tag}-{sha}-html-doc"

    session.log("Adding build info to documentation section")
    build_info_file = Path("docs/about/build.template.md")
    build_info = build_info_file.read_text()
    build_info = (
        build_info.replace("__SHA__", sha)
        .replace("__TAG__", tag)
        .replace("__DATE__", date)
    )
    build_info_file.parent.joinpath("build.md").write_text(build_info)
    build_info_file.unlink()

    session.log(f"Current dir: {Path.cwd()}")
    session.log(f"Building documentation: {doc_name}")

    session.install("zensical", "mkdocstrings-python")
    session.run("pip", "list")
    session.run("zensical", "build", "-f", str(Path.cwd() / "zensical.toml"))

    if os.getenv("CI") == "true":
        session.log("compressing documentation")
        shutil.make_archive(
            f"documentation-{doc_name}", "zip", root_dir=".", base_dir="site"
        )
