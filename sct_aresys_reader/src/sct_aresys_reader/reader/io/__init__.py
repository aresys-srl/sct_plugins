# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""I/O management package."""

from sct_aresys_reader.reader.io.channel_iteration import iter_channels
from sct_aresys_reader.reader.io.io_support import (
    create_new_metadata,
    read_metadata,
    read_raster,
    read_raster_with_raster_info,
    write_metadata,
    write_raster,
    write_raster_with_raster_info,
)
from sct_aresys_reader.reader.io.point_target_binary import (
    PointSetProduct,
    convert_array_to_point_target_structure,
)
from sct_aresys_reader.reader.io.point_target_file import read_point_targets_file, write_point_targets_file
from sct_aresys_reader.reader.io.productfolder2 import create_product_folder, open_product_folder


class ChannelDeprecationWarning(Warning):
    """Custom deprecation warning for the Channel class"""


class ProductFolderDeprecationWarning(Warning):
    """Custom deprecation warning for the ProductFolder class"""


class RenameProductFolderDeprecationWarning(ProductFolderDeprecationWarning):
    """Custom deprecation warning for the rename_product_folder function"""


class RemoveProductFolderDeprecationWarning(ProductFolderDeprecationWarning):
    """Custom deprecation warning for the remove_product_folder function"""


__all__ = [
    "iter_channels",
    "create_orbit",
    "create_new_metadata",
    "read_metadata",
    "read_raster",
    "read_raster_with_raster_info",
    "write_metadata",
    "write_raster",
    "write_raster_with_raster_info",
    "PointSetProduct",
    "convert_array_to_point_target_structure",
    "read_point_targets_file",
    "write_point_targets_file",
    "create_product_folder",
    "open_product_folder",
    "read_swath_table",
    "write_swath_table_xml",
    "read_timeline_table",
    "write_timeline_table_xml",
    "read_trajectory",
    "write_trajectory_xml",
    "read_sat_table",
]
