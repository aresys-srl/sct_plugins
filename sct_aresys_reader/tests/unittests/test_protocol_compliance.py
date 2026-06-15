# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT Aresys Product Format Reader Plugin - Testing Plugin Protocol Compliance
"""

from __future__ import annotations

import pytest
from arepytools.io.productfolder2 import is_product_folder as is_aresys_product
from perseo_quality.io.quality_input_protocol import ChannelData, SARCoordinatesFunction
from sct.io.extended_protocols import SCTInputProduct
from sct.plugins.loader import import_input_product_plugins

from sct_aresys_reader.protocol_implementation import (
    ChannelManager,
    DopplerPolynomialWrapper,
    ProductFolderManagerExtended,
)


@pytest.fixture
def plugin():
    return import_input_product_plugins()


class TestPluginProtocolCompliance:
    """Test Plugin Protocol Compliance"""

    def test_installed_plugin(self, plugin) -> None:
        """Testing correct plugin installation"""
        assert len(plugin) == 1
        assert plugin[0].__name__ == "AresysInputProductPlugin"

    def test_get_manager(self, plugin) -> None:
        """Testing manager protocol compliance"""
        assert plugin[0].get_manager() is ProductFolderManagerExtended
        assert isinstance(plugin[0].get_manager(), SCTInputProduct)

    def test_get_detector(self, plugin) -> None:
        """Testing detector protocol compliance"""
        assert plugin[0].get_detector() is is_aresys_product

    def test_get_ale_corrector(self, plugin) -> None:
        """Testing ALE Corrector protocol compliance"""
        assert plugin[0].get_ale_corrector() is None

    def test_product_protocol_compliance(self) -> None:
        """Testing product protocol implementation compliance"""
        assert isinstance(ProductFolderManagerExtended, SCTInputProduct)

    def test_channel_protocol_compliance(self) -> None:
        """Testing channel protocol implementation compliance"""
        assert isinstance(ChannelManager, ChannelData)

    def test_polynomial_protocol_compliance(self) -> None:
        """Testing polynomial protocol implementation compliance"""
        assert isinstance(DopplerPolynomialWrapper, SARCoordinatesFunction)
