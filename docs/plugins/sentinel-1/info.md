---
icon: lucide/plug-2
---

# Plugin

This plugin is designed to process SAR Level 1 A/B Sentinel-1 products from the ESA Sentinel-1 satellite missions.
It supports all active and past missions, naming A, B, C and D sensors.

==Plugin name:== ``sct-sentinel1-reader``

The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the Sentinel-1 product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported Sentinel-1 acquisition modes:

- **STRIPMAP**
- **TOPSAR**
- **WAVE**
