# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT SAOCOM Product Format Reader Plugin - Testing Plugin Protocol Compliance
"""

from __future__ import annotations

import unittest

from arepyextras.eo_products.saocom.l1_products.utilities import is_saocom_product
from arepyextras.quality.io.quality_input_protocol import ChannelData, SARCoordinatesFunction
from sct.io.extended_protocols import SCTInputProduct
from sct.io.input_product_plugins import import_input_product_plugins

from sct_saocom_reader.protocol_implementation import (
    SAOCOMChannelManager,
    SAOCOMDopplerPolynomial,
    SAOCOMProductManager,
)


class PluginProtocolComplianceTest(unittest.TestCase):
    """Test Plugin Protocol Compliance"""

    def setUp(self):
        self.plugin = import_input_product_plugins([])

    def test_installed_plugin(self) -> None:
        """Testing correct plugin installation"""
        self.assertEqual(len(self.plugin), 1)
        self.assertEqual(self.plugin[0].__name__, "sct_saocom_reader")

    def test_get_manager(self) -> None:
        """Testing manager protocol compliance"""
        isinstance(self.plugin[0].get_manager(), SAOCOMProductManager)
        isinstance(self.plugin[0].get_manager(), SCTInputProduct)

    def test_get_detector(self) -> None:
        """Testing detector protocol compliance"""
        self.assertTrue(self.plugin[0].get_detector() is is_saocom_product)

    def test_get_ale_corrector(self) -> None:
        """Testing ALE Corrector protocol compliance"""
        self.assertIsNone(self.plugin[0].get_ale_corrector())

    def test_product_protocol_compliance(self) -> None:
        """Testing product protocol implementation compliance"""
        isinstance(SAOCOMProductManager, SCTInputProduct)

    def test_channel_protocol_compliance(self) -> None:
        """Testing channel protocol implementation compliance"""
        isinstance(SAOCOMChannelManager, ChannelData)

    def test_polynomial_protocol_compliance(self) -> None:
        """Testing polynomial protocol implementation compliance"""
        isinstance(SAOCOMDopplerPolynomial, SARCoordinatesFunction)


if __name__ == "__main__":
    unittest.main()
