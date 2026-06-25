# SCT Product Format Plugins

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![ASAR: GPL-3.0](https://img.shields.io/badge/ASAR%20License-GPL--3.0-blue.svg)](#license)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://python.org)
[![GitHub Release](https://img.shields.io/github/v/release/aresys-srl/sct_plugins)](https://github.com/aresys-srl/sct_plugins/releases)
[![Docs](https://img.shields.io/badge/docs-github.io-blue)](https://aresys-srl.github.io/sct_plugins)

**SAR** L1 Product Format plugins collection for [SCT (SAR Calibration Toolbox)](https://github.com/aresys-srl/sct).

This repository is a monorepo consisting of several standalone Python packages, each dedicated to reading and
interpreting Level 1 product formats from a specific SAR sensor/mission. Plugins integrate with SCT via a
unified protocol, enabling all analyses regardless of the input format.

## Available Plugins

| Package | PyPI | CI | Description |
|---------|------|----|-------------|
| **sct-sentinel1-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-sentinel1-reader)](https://pypi.org/project/sct-sentinel1-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/sentinel1.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/sentinel1.yml) | Sentinel-1 (A/B/C/D) Level 1 products |
| **sct-novasar1-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-novasar1-reader)](https://pypi.org/project/sct-novasar1-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/novasar1.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/novasar1.yml) | NovaSAR-1 Level 1 products |
| **sct-saocom-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-saocom-reader)](https://pypi.org/project/sct-saocom-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/saocom.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/saocom.yml) | Saocom Level 1 products |
| **sct-iceye-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-iceye-reader)](https://pypi.org/project/sct-iceye-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/iceye.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/iceye.yml) | ICEYE Level 1 products |
| **sct-radarsat2-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-radarsat2-reader)](https://pypi.org/project/sct-radarsat2-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/radarsat2.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/radarsat2.yml) | RADARSAT-2 Level 1 products |
| **sct-eos04-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-eos04-reader)](https://pypi.org/project/sct-eos04-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/eos04.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/eos04.yml) | EOS-04 Level 1 products |
| **sct-cosmo-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-cosmo-reader)](https://pypi.org/project/sct-cosmo-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/cosmo.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/cosmo.yml) | COSMO-SkyMed Level 1 products |
| **sct-asar-reader** ⚠️ | [![PyPI](https://img.shields.io/pypi/v/sct-asar-reader)](https://pypi.org/project/sct-asar-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/asar.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/asar.yml) | ENVISAT/ERS ASAR Level 1 products |
| **sct-aresys-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-aresys-reader)](https://pypi.org/project/sct-aresys-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/aresys.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/aresys.yml) | Aresys internal Level 1 product format |
| **sct-strix-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-strix-reader)](https://pypi.org/project/sct-strix-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/strix.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/strix.yml) | Synspective StriX Level 1 products |
| **sct-terrasarx-reader** | [![PyPI](https://img.shields.io/pypi/v/sct-terrasarx-reader)](https://pypi.org/project/sct-terrasarx-reader/) | [![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/terrasarx.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/terrasarx.yml) | TerraSAR-X Level 1 products |
| **sct-biomass-reader** | TBD | TBD | Biomass Level 1 products |

## Documentation

Full documentation is available at [https://aresys-srl.github.io/sct_plugins](https://aresys-srl.github.io/sct_plugins).

## Installation

Each plugin is a standalone Python package available on [PyPI](https://pypi.org/user/aresys/) and can be installed
using ``pip``:

```bash
pip install <package-name>
```

## License

All plugins in this repository are licensed under the **MIT License**, except for the following:

| Package | License |
|---------|---------|
| **sct-asar-reader** | **GNU General Public License v3.0 or later (GPL-3.0-or-later)** |

> [!WARNING]
> Using the ``sct-asar-reader`` plugin in a project may require the combined work to comply with the terms of
> the GPL-3.0 license. Please review the GPL-3.0 license before integrating this package into your project.

## Contributing

Contributions are welcome! If you encounter a bug, have a feature request, or want to contribute code:

- **Report bugs & request features**: open an issue on [GitHub](https://github.com/aresys-srl/sct_plugins/issues).
  Include a clear description, steps to reproduce, and your environment details.
- **Submit changes**: fork the repository, create a feature branch, and open a pull request. Ensure your code passes
  the existing linting and test suite.
- **Questions**: use GitHub Discussions for general questions and discussions.

## Copyright

Copyright &copy; 2026-present Aresys S.r.l. <info@aresys.it>
