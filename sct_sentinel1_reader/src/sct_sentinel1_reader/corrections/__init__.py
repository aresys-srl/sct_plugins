# SPDX-FileCopyrightText: Aresys S.r.l. <info@aresys.it>
# SPDX-License-Identifier: MIT

"""
Sentinel-1 ALE Corrections
--------------------------
"""

ALE_CORRECTIONS_FIELDS = {
    "etad_range": "ext_range_correction_[m]",
    "etad_azimuth": "ext_azimuth_correction_[m]",
    "rng_doppler_shift": "doppler_shift_range_correction_[m]",
    "az_fmrate_shift": "fm_rate_shift_azimuth_correction_[m]",
    "az_instrument_timing": "instrument_timing_azimuth_correction_[m]",
    "az_bistatic_delay": "bistatic_delay_azimuth_correction_[m]",
}
