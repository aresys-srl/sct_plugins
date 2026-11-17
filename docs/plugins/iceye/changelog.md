---
icon: lucide/history
---

# Changelog

## Unreleased

- Support for ICEYE SLC-COG and GRD-COG products (requires the `eo-products` release adding ICEYE COG support):
  channel metadata and raster files are selected by file type instead of by number of channel files, and the COG
  raster layout is forwarded to the raster reader.

## v1.0.1

- Relaxing ``perseo``, ``eo-products`` and ``sct`` dependencies constraints.

## v1.0.0

First official release.
