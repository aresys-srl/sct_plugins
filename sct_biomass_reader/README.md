# SCT Plugin: Biomass Products reader

[![PyPI version](https://img.shields.io/pypi/v/sct-biomass-reader)](https://pypi.org/project/sct-biomass-reader/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
[![CI](https://github.com/aresys-srl/sct_plugins/actions/workflows/biomass.yml/badge.svg)](https://github.com/aresys-srl/sct_plugins/actions/workflows/biomass.yml)

[SCT (SAR Calibration Toolbox)](https://github.com/aresys-srl/sct) plugin for reading Biomass
Level 1 products, both L1A (SLC) and L1B (GRD). This package integrates with SCT through its
input products plugin system, enabling all SCT analyses on Biomass data.

## Supported Acquisition Modes

- **Stripmap**

## Installation

This plugin requires `bps-transcoder>=4.5.0`, a package distributed as part of the [BIOMASS Processing Suite (BPS)](https://github.com/BioPAL/BPS).

> [!TIP]
> We strongly recommend installing the plugin in a dedicated Conda environment to avoid dependency conflicts and ensure a reproducible installation.

To ensure a proper installation of bps-transcoder and all its dependencies, including `GDAL`, install it using conda:

```bash
conda install biomass-bps::bps-transcoder
```

Once the installation is complete, activate the same Conda environment and install the plugin using `pip`:

```bash
pip install sct-biomass-reader
```

SCT is automatically installed as a dependency.

## Compatibility

This plugin must be installed in the same Python environment as SCT. Once installed,
the plugin is automatically discovered and registered by SCT through its entry-point
based plugin system; no additional configuration is required.

## Documentation

- [SCT documentation](https://opensource.aresys.it/sct/)
- [Plugins documentation](https://opensource.aresys.it/sct_plugins)
- [BIOMASS Processing Suite (BPS)](https://www.biomass-disc.info/release_note)

## License

This project is licensed under the MIT License. See the [LICENSE.txt](LICENSE.txt) file for details.

Copyright &copy; 2026-present Aresys S.r.l. <info@aresys.it>
