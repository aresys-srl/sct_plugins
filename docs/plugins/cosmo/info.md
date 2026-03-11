---
icon: lucide/plug-2
---

# Plugin

This python package is a plugin designed for **Sar Calibration Toolbox (SCT)** to allow quality processing on COSMO-SkyMed L1
products, both L1-A and L1-B.

==Plugin name:== ``sct-cosmo-reader``

The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the COSMO-SkyMed product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported COSMO-SkyMed acquisition modes:

- **STRIPMAP**
- **SCANSAR**
- **SPOTLIGHT**
