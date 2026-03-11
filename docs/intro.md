---
icon: lucide/satellite
---

# Introduction

Plugins are python packages that can be used to read data from different sensors.

The **SCT software itself does not natively support any specific format of Level 1 SAR products**. Instead, it has been
designed to abstract away the dependency on the input format, relying solely on a generic *Python protocol*.
Once this protocol is satisfied, it enables the execution of all implemented analyses regardless of the type of input
product.

!!! warning

    Only ==L1 products (both L1-A and L1-B)== for each implemented sensor plugin are supported.

To handle the implementation of the methods and properties defined by the protocol, custom Python packages are used,
each dedicated to a particular sensor or format. These packages, managed as plugins by the software, are solely responsible
for assembling the information read from the product in its specific format, processing it, and ensuring that all the
functionalities required by the protocol are implemented.

This allows:

- New input product formats to be added without modifying the core analysis code.
- Analyses to interact with a unified interface, regardless of the actual product type.
- Easy distribution of input product plugins as independent packages.

!!! note

    To use the functionalities of SCT for a specific product, it is necessary to install, in addition to SCT, the
    corresponding plugin.

## Architecture and internal structure

The plugin architecture is described in detail in the [Plugin Architecture](./architecture/index.md) section while the
internal structure is described in the [Internal Structure](./architecture/internal.md) section.

## Benefits

- **Extensibility**: New input products are supported via independent packages.
- **Decoupling**: Core analysis logic does not depend on plugin implementation.
- **Testability**: Plugins can be mocked or substituted without touching the core.
- **Dynamic discovery**: Plugins are discovered at runtime via entry points, no hard-coded imports required.

## Plugin Discovery

Plugins are discovered dynamically using [OpenStack's stevedore](https://docs.openstack.org/).

> Refer to the [Plugin Discovery](./architecture/internal.md#plugin-discovery) paragraph for more details.
