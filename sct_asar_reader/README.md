# SCT Plugin: ENVISAT/ERS ASAR format reader

[![PyPI version](https://img.shields.io/pypi/v/sct-asar-reader)](https://pypi.org/project/sct-asar-reader/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://python.org)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE.txt)

[![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/asar.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/asar.yml)

[SCT (SAR Calibration Toolbox)](https://github.com/aresys-srl/sct) plugin for reading ENVISAT/ERS
Level 1 ASAR products, both L1A (SLC) and L1B (GRD). This package integrates with SCT through
its input products plugin system, enabling all SCT analyses on ENVISAT/ERS ASAR data.

## Supported Acquisition Modes

- **Stripmap**
- **Scansar**

## Installation

```bash
pip install sct-asar-reader
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

This project is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.
See the [LICENSE.txt](LICENSE.txt) file for details.

> [!WARNING]
> Installing this plugin may require your combined work to comply with the terms of the
> GPL-3.0 license. Please review the GPL-3.0 license before integrating this package
> into your project.

Copyright &copy; 2026-present Aresys S.r.l. <info@aresys.it>
