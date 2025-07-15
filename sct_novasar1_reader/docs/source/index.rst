.. _docs_mainpage:

##################################
SCT NovaSAR1 Level 1 Reader Plugin
##################################

.. toctree::
   :maxdepth: 2
   :hidden:

   install  
   reference/api/index
   changelog

This python package is a plugin designed for **Sar Calibration Toolbox (SCT)** to allow quality processing on NovaSAR1 L1
products, both L1-A and L1-B.
The main purpose of this package is to provide an SCT input protocol compliant object properly wrapping and composing
the NovaSAR1 product info allowing a seamless processing of this product format for every analysis integrated in the tool.

Supported NovaSAR1 acquisition modes:

- **STRIPMAP**
- **SCANSAR**
