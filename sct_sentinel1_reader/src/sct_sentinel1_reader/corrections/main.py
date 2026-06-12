# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""ALE Corrector for Sentinel-1 products."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
from sct.analyses.point_target.config import SCTPointTargetAnalysisCorrectionsConf
from sct.io.extended_protocols import ALECorrectionFunctionType

from sct_sentinel1_reader.corrections import ALE_CORRECTIONS_FIELDS
from sct_sentinel1_reader.corrections.custom_corrections import (
    compute_corrections,
)
from sct_sentinel1_reader.corrections.etad_corrections_main import get_etad_corrections


class S1ALECorrector:
    """Class to manage Absolute Localization Errors corrections form external products or internal models"""

    def __init__(self, external_product_path: Path | None):
        self._etad_product = external_product_path

    @property
    def additional_corrections_fields(self) -> list[str]:
        """List of all possible additional corrections fields that can be added to the output dataframe"""
        return list(ALE_CORRECTIONS_FIELDS.values())

    def get_ale_corrections_function(self) -> ALECorrectionFunctionType:
        """Retrieving proper Absolute Localization Error corrections function. Returning ETAD corrections if ETAD
        product path is provided, Sentinel1 IPF sensor specific corrections otherwise.

        Returns
        -------
        ALECorrectionFunctionType
            function to compute ALE corrections
        """
        if self._etad_product is not None:

            def func(_: Path, data: pd.DataFrame) -> pd.DataFrame:
                return get_etad_corrections(etad_product_path=self._etad_product, data=data)

            return func
        return compute_corrections

    def update_corrections_config(
        self, corrections_config: SCTPointTargetAnalysisCorrectionsConf
    ) -> SCTPointTargetAnalysisCorrectionsConf:
        """Updating the SCT Point Target Analysis corrections configuration to disable additional corrections when using
        ETAD products.

        Parameters
        ----------
        corrections_config : SCTPointTargetAnalysisCorrectionsConf
            original PTA corrections configuration

        Returns
        -------
        SCTPointTargetAnalysisCorrectionsConf
            updated PTA corrections configuration
        """
        if self._etad_product:
            new_config = deepcopy(corrections_config)
            new_config.enable_solid_tides_correction = False
            new_config.enable_ionospheric_correction = False
            new_config.enable_tropospheric_correction = False
            new_config.enable_sensor_specific_processing_corrections = False
            return new_config
        return corrections_config
