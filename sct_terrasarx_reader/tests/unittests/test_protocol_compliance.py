# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT TerraSAR-X Product Format Reader Plugin - Testing Plugin Protocol Compliance
"""

from __future__ import annotations

import unittest

from eo_products.terrasarx.utilities import is_terrasarx_product
from perseo_quality.io.quality_input_protocol import ChannelData, SARCoordinatesFunction
from sct.io.extended_protocols import SCTInputProduct
from sct.io.input_product_plugins import import_input_product_plugins

from sct_terrasarx_reader.protocol_implementation import (
    TERRASARXChannelManager,
    TERRASARXDopplerPolynomial,
    TERRASARXProductManager,
)


class PluginProtocolComplianceTest(unittest.TestCase):
    """Test Plugin Protocol Compliance"""

    def setUp(self):
        self.plugin = import_input_product_plugins(additional_plugins=[])

    def test_installed_plugin(self) -> None:
        """Testing correct plugin installation"""
        self.assertEqual(len(self.plugin), 1)
        self.assertEqual(self.plugin[0].__name__, "sct_terrasarx_reader")

    def test_get_manager(self) -> None:
        """Testing manager protocol compliance"""
        isinstance(self.plugin[0].get_manager(), TERRASARXProductManager)
        isinstance(self.plugin[0].get_manager(), SCTInputProduct)

    def test_get_detector(self) -> None:
        """Testing detector protocol compliance"""
        self.assertTrue(self.plugin[0].get_detector() is is_terrasarx_product)

    def test_get_ale_corrector(self) -> None:
        """Testing ALE Corrector protocol compliance"""
        self.assertIsNone(self.plugin[0].get_ale_corrector())

    def test_product_protocol_compliance(self) -> None:
        """Testing product protocol implementation compliance"""
        isinstance(TERRASARXProductManager, SCTInputProduct)

    def test_channel_protocol_compliance(self) -> None:
        """Testing channel protocol implementation compliance"""
        isinstance(TERRASARXChannelManager, ChannelData)

    def test_polynomial_protocol_compliance(self) -> None:
        """Testing polynomial protocol implementation compliance"""
        isinstance(TERRASARXDopplerPolynomial, SARCoordinatesFunction)


if __name__ == "__main__":
    unittest.main()
