---
icon: lucide/rocket
---

# Overview

Welcome to the official Product Format Plugins documentation for the [SCT (SAR Calibration Toolbox)](https://opensource.aresys.it/sct/)
python ecosystem.

This documentation hub collects the documentation for all the input Product Format plugins developed so far, providing
a small overview of the functionalities of input plugins, their structure and usage and the python API references.

<figure markdown="span">
    ![Plugin Mechanism](./assets/images/plugin_mechanism.png){ width="850" }
    <figcaption>Plugin discovery mechanism in SCT.</figcaption>
</figure>

Here you will find:

* A list of all the input plugins available in the ecosystem
* Description of the plugins system and architecture
* A guide to create your own plugins

## Available Plugins

Here is an up-to-date list of the available plugins:

| Sensor Name | Package Name | Documentation |
| ----------- | --------- | --------- |
| Sentinel-1 (A,B,C,D) | *sct-sentinel1-reader* | [Sentinel-1 Plugin](./plugins/sentinel-1/info.md) |
| Saocom | *sct-saocom-reader* | [Saocom Plugin](./plugins/saocom/info.md) |
| NovaSAR1 | *sct-novasar1-reader* | [NovaSAR1 Plugin](./plugins/novasar-1/info.md) |
| Cosmo Sky-Med | *sct-cosmo-reader* | [Cosmo Plugin](./plugins/cosmo/info.md) |
| RadarSAT-2 | *sct-radarsat2-reader* | [RadarSAT-2 Plugin](./plugins/radarsat-2/info.md) |
| ICEYE | *sct-iceye-reader* | [ICEYE Plugin](./plugins/iceye/info.md) |
| Aresys | *sct-aresys-reader* | [Aresys Plugin](./plugins/aresys/info.md) |
| ERS/ENVISAT | *sct-asar-reader* | [ASAR Plugin](./plugins/asar/info.md) |

## Installation

Each plugin can be installed separately as it is a full fledged standalone python package. All plugins are available on
[PyPI](https://pypi.org/user/aresys/) and can be installed using ``pip``.

> Refer to the [installation](./install.md) page for more details.
