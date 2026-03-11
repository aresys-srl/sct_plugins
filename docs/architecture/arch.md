---
icon: lucide/landmark
---

# Plugin Architecture

SCT supports multiple satellite product formats through a **plugin-based architecture**.
Instead of embedding format-specific logic directly in the core library, input products are handled by **external plugin packages**
that implement a common interface.

This page explains how to create and distribute a new **Input Product Plugin** for SCT.

## Overview

An SCT input product plugin is a **separate Python package** that:

1. Implements the ``sct.plugins.protocols.InputProductPluginProtocol``.
2. Exposes the plugin class through a **Python entry point** in the ``sct.input_products`` namespace.
3. Is installed alongside SCT so it can be **automatically discovered**.

Once installed, SCT will detect the plugin at runtime and make it available to the analysis pipeline.

??? info "Format Reader vs Plugin"

    The plugin itself does not necessarily need to implement all the low-level logic required to read the input product.
    In many cases, existing plugins rely on external libraries, which are not part of the core SCT package, to handle the
    parsing and loading of the native product format. The plugin acts primarily as an adapter layer: it uses external
    tools or libraries to access the product data and then reorganizes and exposes the relevant information so that it
    conforms to the SCT internal data model required by the analyses.

## Package Structure

A minimal plugin package may look like the following:

```
📁 root
├── 📁 src
│   └── 📁 sct_<product_name>_reader
│       ├── 🐍 __init__.py
│       ├── 🐍 interface.py
│       └── 🐍 protocol_implementation.py
├── ⚙️ pyproject.toml
├── 📄 LICENSE.txt
└── 📄 README.md
```

Typical responsibilities:

- ``interface.py``: defines the plugin class implementing the SCT Plugin protocol.
- ``protocol_implementation.py``: contains the SCT Input Product protocol implementation logic.
- ``pyproject.toml``: declares the plugin entry point.
