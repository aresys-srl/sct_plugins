# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT Sentinel-1 Reader Plugin - Testing Plugin Protocol Compliance
"""

from __future__ import annotations

import unittest

from eo_products.sentinel1.utilities import is_s1_safe_product
from perseo_quality.io.quality_input_protocol import ChannelData, SARCoordinatesFunction
from sct.io.extended_protocols import SCTInputProduct
from sct.plugins.loader import import_input_product_plugins
from sct.plugins.protocols import AbsoluteLocalizationErrorCorrector

from sct_sentinel1_reader.corrections.main import S1ALECorrector
from sct_sentinel1_reader.protocol_implementation import (
    Sentinel1ChannelManager,
    Sentinel1DopplerPolynomial,
    Sentinel1ProductManager,
)


class PluginProtocolComplianceTest(unittest.TestCase):
    """Test Plugin Protocol Compliance"""

    def setUp(self):
        self.plugin = import_input_product_plugins()

    def test_installed_plugin(self) -> None:
        """Testing correct plugin installation"""
        self.assertEqual(len(self.plugin), 1)
        self.assertEqual(self.plugin[0].__name__, "Sentinel1InputProductPlugin")

    def test_get_manager(self) -> None:
        """Testing manager protocol compliance"""
        isinstance(self.plugin[0].get_manager(), Sentinel1ProductManager)
        isinstance(self.plugin[0].get_manager(), SCTInputProduct)

    def test_get_detector(self) -> None:
        """Testing detector protocol compliance"""
        self.assertTrue(self.plugin[0].get_detector() is is_s1_safe_product)

    def test_get_ale_corrector(self) -> None:
        """Testing ALE Corrector protocol compliance"""
        isinstance(self.plugin[0].get_ale_corrector(), S1ALECorrector)
        isinstance(self.plugin[0].get_ale_corrector(), AbsoluteLocalizationErrorCorrector)

    def test_product_protocol_compliance(self) -> None:
        """Testing product protocol implementation compliance"""
        isinstance(Sentinel1ProductManager, SCTInputProduct)

    def test_channel_protocol_compliance(self) -> None:
        """Testing channel protocol implementation compliance"""
        isinstance(Sentinel1ChannelManager, ChannelData)

    def test_polynomial_protocol_compliance(self) -> None:
        """Testing polynomial protocol implementation compliance"""
        isinstance(Sentinel1DopplerPolynomial, SARCoordinatesFunction)


if __name__ == "__main__":
    unittest.main()
