---
icon: lucide/history
---

# Changelog

# v1.0.5

**Bug Fixing**

- Fixed a bug when loading a SLC product not having the ``GroundToSlantVector`` or ``SlantToGroundVector`` metadata.

# v1.0.4

**Bug Fixing**

- Fixed a bug when accessing missing ``attitude_info``.

**Other Changes**

- Removed unused `pulse` info from ``ChannelManager``.

# v1.0.3

**Other Changes**

- Removing internal format reader code from the plugin package in favor of ``aresys-io`` dependency.

# v1.0.2

**Bug Fixing**

- Fixed a bug where the image radiometric quantity was incorrectly set in ``ChannelManager``

## v1.0.1

- Relaxing ``perseo`` and ``sct`` dependencies constraints.

## v1.0.0

First official release.
