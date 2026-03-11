---
icon: lucide/plug-2
---

# Plugin

This python package is a plugin designed for **Sar Calibration Toolbox (SCT)** to allow quality processing on
ENVISAT/ERS L1 products in ASAR format, both L1-A and L1-B.

==Plugin name:== ``sct-asar-reader``

The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the ENVISAT/ERS product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported ENVISAT/ERS acquisition modes:

- **STRIPMAP**
- **SCANSAR**

!!! warning "License"

    This plugin is licensed under the [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html). This means that
    installing this plugin changes the license of the SCT software from MIT to GPL-3.0.
