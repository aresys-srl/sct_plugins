---
icon: lucide/plug-2
---

# Plugin

This python package is a plugin designed for **Sar Calibration Toolbox (SCT)** to allow quality processing on Synspective
STRIX L1 products, both L1-A and L1-B.

==Plugin name:== ``sct-strix-reader``

The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the STRIX product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported STRIX acquisition modes:

- **STRIPMAP**
- **SPOTLIGHT** (both *SLIDING* and *STARING*)
