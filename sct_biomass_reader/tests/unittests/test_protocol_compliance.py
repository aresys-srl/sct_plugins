# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
SCT Biomass Product Format Reader Plugin - Testing Plugin Protocol Compliance
"""

from __future__ import annotations

import unittest
from pathlib import Path

from arepyextras.quality.io.quality_input_protocol import ChannelData, SARCoordinatesFunction
from sct.io.extended_protocols import SCTInputProduct
from sct.io.input_product_plugins import import_input_product_plugins

from sct_biomass_reader.protocol_implementation import (
    BiomassChannelManager,
    BiomassL1ProductManager,
    DopplerPolynomialWrapper,
)


class PluginProtocolComplianceTest(unittest.TestCase):
    """Test Plugin Protocol Compliance"""

    def setUp(self) -> None:
        self.plugin = import_input_product_plugins([])

    def test_installed_plugin(self) -> None:
        """Testing correct plugin installation"""
        self.assertEqual(len(self.plugin), 1)
        self.assertEqual(self.plugin[0].__name__, "sct_biomass_reader")

    def test_get_manager(self) -> None:
        """Testing manager protocol compliance"""
        isinstance(self.plugin[0].get_manager(), BiomassL1ProductManager)
        isinstance(self.plugin[0].get_manager(), SCTInputProduct)

    def test_get_detector(self) -> None:
        """Testing detector protocol compliance"""
        detector = self.plugin[0].get_detector()
        self.assertTrue(callable(detector))
        self.assertFalse(detector(Path("/some/path")))
        self.assertFalse(detector("/some/path"))
        self.assertTrue(
            detector(Path("BIO_S1_SCS__1S_20250607T094418_20250607T094438_C_G___M___C___T____F166_01_D9VA9E")),
        )

    def test_get_ale_corrector(self) -> None:
        """Testing ALE Corrector protocol compliance"""
        self.assertIsNone(self.plugin[0].get_ale_corrector())

    def test_product_protocol_compliance(self) -> None:
        """Testing product protocol implementation compliance"""
        isinstance(BiomassL1ProductManager, SCTInputProduct)

    def test_channel_protocol_compliance(self) -> None:
        """Testing channel protocol implementation compliance"""
        isinstance(BiomassChannelManager, ChannelData)

    def test_polynomial_protocol_compliance(self) -> None:
        """Testing polynomial protocol implementation compliance"""
        isinstance(DopplerPolynomialWrapper, SARCoordinatesFunction)


if __name__ == "__main__":
    unittest.main()
