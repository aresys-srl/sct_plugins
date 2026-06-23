# SCT Plugin: Sentinel-1 format reader

[![PyPI version](https://img.shields.io/pypi/v/sct-sentinel1-reader)](https://pypi.org/project/sct-sentinel1-reader/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

[![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/sentinel1.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/sentinel1.yml)

[SCT (SAR Calibration Toolbox)](https://github.com/aresys-srl/sct) plugin for reading Sentinel-1
Level 1 products, both L1A (SLC) and L1B (GRD), from ESA Sentinel-1 satellite missions
(A, B, C, D). This package integrates with SCT through its input products plugin system,
enabling all SCT analyses on Sentinel-1 data.

## Supported Acquisition Modes

- **Stripmap** (SM)
- **TOPSAR** (IW, EW)
- **WAVE** (WV)

## Installation

```bash
pip install sct-sentinel1-reader
```

SCT is automatically installed as a dependency.

## Compatibility

This plugin must be installed in the same Python environment as SCT. Once installed,
the plugin is automatically discovered and registered by SCT through its entry-point
based plugin system; no additional configuration is required.

## Documentation

- [SCT documentation](https://aresys-srl.github.io/sct/)
- [Plugins documentation](https://aresys-srl.github.io/sct_plugins)

## License

This project is licensed under the MIT License. See the [LICENSE.txt](LICENSE.txt) file for details.

Copyright &copy; 2026-present Aresys S.r.l. <info@aresys.it>
