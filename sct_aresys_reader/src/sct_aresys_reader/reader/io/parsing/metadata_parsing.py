# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Metadata parsing
----------------
"""

from sct_aresys_reader.reader.io import metadata
from sct_aresys_reader.reader.io.parsing import metadata_models
from sct_aresys_reader.reader.io.parsing.parsing import parse, serialize
from sct_aresys_reader.reader.io.parsing.translate import (
    translate_metadata_from_model,
    translate_metadata_to_model,
)


def serialize_metadata(metadata_obj: metadata.MetaData) -> str:
    """Serialize metadata object

    Parameters
    ----------
    metadata_obj : metadata.MetaData
        metadata representation object

    Returns
    -------
    str
        serialized metadata as a string (xml format)
    """
    metadata_model = translate_metadata_to_model(metadata_obj)
    return serialize(metadata_model)


def parse_metadata(metadata_content: str) -> metadata.MetaData:
    """Parse metadata XML string

    Parameters
    ----------
    metadata_content : str
        Metadata as string in XML format

    Returns
    -------
    metadata.MetaData
        metadata representation object
    """
    metadata_model: metadata_models.AresysXmlDoc = parse(metadata_content, metadata_models.AresysXmlDoc)
    return translate_metadata_from_model(metadata_model)
