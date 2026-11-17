# SPDX-License-Identifier: MIT

"""SCT ICEYE Product Format Reader Plugin - Testing SLC-COG and GRD-COG channels."""

from __future__ import annotations

import eo_products.iceye.utilities as eo_iceye_utilities
import numpy as np
import pytest
from perseo_quality.core.generic_dataclasses import SARProjection, SARRadiometricQuantity, SARSideLooking
from perseo_quality.core.signal_processing import radiometric_correction
from scipy.constants import speed_of_light

from sct_iceye_reader.interface import ICEYEProductPlugin
from sct_iceye_reader.protocol_implementation import ICEYEProductManager

from .synthetic_cog import (
    CALIBRATION_FACTOR,
    GROUND_TO_SLANT_COEFF,
    INCIDENCE_COEFF,
    LINES,
    RANGE_NEAR,
    RANGE_SAMPLING_RATE,
    SAMPLES,
    expected_samples,
    write_cog,
)

# ICEYE COG support needs an eo_products release that reads SLC-COG/GRD-COG products
pytestmark = pytest.mark.skipif(
    not hasattr(eo_iceye_utilities, "ICEYERasterLayout"), reason="installed eo_products cannot read ICEYE COG products"
)


def _read_block(channel, azimuth_index, range_index, size, **kwargs):
    """read_data block and the corresponding (first line, first sample)"""
    data = channel.read_data(azimuth_index=azimuth_index, range_index=range_index, cropping_size=size, **kwargs)
    return data, azimuth_index - size[1] // 2, range_index - size[0] // 2


@pytest.mark.parametrize("look", ["right", "left"])
def test_slc_cog_channel(tmp_path, look):
    write_cog(tmp_path, level="SLC", look=look)
    assert ICEYEProductPlugin.get_detector()(tmp_path)
    product = ICEYEProductManager(tmp_path)
    assert product.channels_list == ["slc_spotlight_vv"]
    channel = product.get_channel_data("slc_spotlight_vv")

    assert channel.projection == SARProjection.SLANT_RANGE
    assert channel.looking_side == SARSideLooking(look.upper())
    assert channel.range_axis[0] == pytest.approx(2 * RANGE_NEAR / speed_of_light, rel=1e-15)
    assert channel.range_step_m == pytest.approx(speed_of_light / (2 * RANGE_SAMPLING_RATE), rel=1e-12)
    assert channel.azimuth_step_s == pytest.approx(100e-6, rel=1e-12)

    data, line0, sample0 = _read_block(channel, azimuth_index=40, range_index=30, size=(10, 12))
    assert data.shape == (10, 12)  # (samples, lines)
    expected = expected_samples("SLC", look)[line0 : line0 + 12, sample0 : sample0 + 10].T * np.sqrt(CALIBRATION_FACTOR)
    np.testing.assert_allclose(data, expected, rtol=1e-6)

    az_time, rng_time = channel.pixel_to_times_conversion(azimuth_index=40.25, range_index=30.5)
    assert channel.times_to_pixel_conversion(az_time, rng_time) == pytest.approx((40.25, 30.5), abs=1e-6)


@pytest.mark.parametrize("look", ["right", "left"])
def test_grd_cog_channel(tmp_path, look):
    write_cog(tmp_path, level="GRD", look=look)
    product = ICEYEProductManager(tmp_path)
    assert product.channels_list == ["grd_spotlight_vv"]
    channel = product.get_channel_data("grd_spotlight_vv")

    assert channel.projection == SARProjection.GROUND_RANGE
    # GRD-COG amplitude is calibrated to beta nought, unlike legacy GRD (sigma nought)
    assert channel.radiometric_quantity == SARRadiometricQuantity.BETA_NOUGHT
    slant = np.polynomial.Polynomial(GROUND_TO_SLANT_COEFF)(channel.range_axis)
    np.testing.assert_allclose(channel.slant_range_axis, 2 * slant / speed_of_light, rtol=1e-15)

    beta, line0, sample0 = _read_block(channel, 50, 20, (8, 6))
    expected = expected_samples("GRD", look)[line0 : line0 + 6, sample0 : sample0 + 8].T * np.sqrt(CALIBRATION_FACTOR)
    np.testing.assert_allclose(beta, expected, rtol=1e-6)

    # beta nought -> sigma nought with the incidence polynomial evaluated at range pixel indexes
    sigma, _, _ = _read_block(channel, 50, 20, (8, 6), output_radiometric_quantity=SARRadiometricQuantity.SIGMA_NOUGHT)
    incidence = np.polynomial.Polynomial(INCIDENCE_COEFF)(np.arange(sample0, sample0 + 8))
    np.testing.assert_allclose(
        sigma,
        radiometric_correction(
            data=expected,
            incidence_angle=np.deg2rad(incidence),
            input_quantity=SARRadiometricQuantity.BETA_NOUGHT,
            output_quantity=SARRadiometricQuantity.SIGMA_NOUGHT,
        ),
        rtol=1e-6,
    )

    az_time, rng_time = channel.pixel_to_times_conversion(azimuth_index=10.0, range_index=33.0)
    assert channel.times_to_pixel_conversion(az_time, rng_time) == pytest.approx((10.0, 33.0), abs=1e-3)


def test_slc_and_grd_cog_channels_in_same_product(tmp_path):
    write_cog(tmp_path, level="SLC")
    write_cog(tmp_path, level="GRD")
    product = ICEYEProductManager(tmp_path)
    assert sorted(product.channels_list) == ["grd_spotlight_vv", "slc_spotlight_vv"]
    assert product.get_channel_data("slc_spotlight_vv").range_axis.size == SAMPLES
    assert product.get_channel_data("grd_spotlight_vv").azimuth_axis.size == LINES
