---
icon: lucide/plug-2
---

# Plugin

This python package is a plugin designed for **Sar Calibration Toolbox (SCT)** to allow quality processing on Biomass L1
products, both L1-A and L1-B.

==Plugin name:== ``sct-biomass-reader``

The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the Biomass product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported Biomass acquisition modes:

- **STRIPMAP**

## Installation

!!! important "Conda Environment"
    This plugin requires `bps-transcoder>=4.5.0`, a package distributed as part of the
    [BIOMASS Processing Suite (BPS)](https://github.com/BioPAL/BPS).
    We strongly recommend installing the plugin in a dedicated Conda environment to avoid dependency
    conflicts and ensure a reproducible installation.

To ensure a proper installation of bps-transcoder and all its dependencies, including `GDAL`, install it using conda:

```bash
conda install biomass-bps::bps-transcoder
```

Once the installation is complete, activate the same Conda environment and install the plugin using `pip`:

```bash
pip install sct-biomass-reader
```

SCT is automatically installed as a dependency.
