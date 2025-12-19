Changelog
=========

v1.1.3
------

**Additional Features**

- Adding ``get_roll_angle_deg`` method to protocol implementation to be used in PERSEO-Quality Elevation Notch Analysis
- Adding ``get_altitude_m`` method to protocol implementation to be used in PERSEO-Quality Elevation Notch Analysis

v1.1.2
------

**Incompatible Changes**

- Removing ``pulse_rate`` property form protocol implementation

**Additional Features**

- Added a property to ``S1ALECorrector`` class to retrieve the list of all possible additional corrections fields that
  can be added to the output dataframe.

v1.1.1
------

**Incompatible Changes**

- Changing Arepyextras - EO Products dependency with EO Products

v1.1.0
------

**Incompatible Changes**

- Changing Arepyextras-Quality dependency with PERSEO-Quality

v1.0.2
------

**Incompatible Changes**

- Added ETAD ALE corrections computation method and refactored the plugin following the new SCT plugins protocol
- Added sensor name property to protocol implementation

v1.0.1
------

**Incompatible Changes**

- Fix to take into account latest Arepyextras-EO Products updates.

v1.0.0
------

First release version of this plugin.
