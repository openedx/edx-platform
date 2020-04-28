Status
======

Accepted


Context
=======

Settings are confusing right now and there are way too many layers. We have
multiple python settings file that "inherit" from each other. In some cases some
layers of the inheritance tree also pull settings from config files leading to
more confusion.


Decision
========
Rather than having multiple python settings files that override things
differently we will move to just a few python files with most of the settings
variance living in YAML config files that are managed by environment operators.

common.py - This file will house the defaults for all settings that are
referenced in the default installation of the edx-platform.

production.py - This settings file will pull the defaults from common.py and
then override them with settings pulled from a single YAML config file. For the
most part this will be a wholesale replacement for any complex values(dicts,
lists, etc) but for some specific settings they will be additive for now.

eg. ADDITIONAL_INSTALLED_APPS, or ADDITIONAL_MIDDLEWARE

Consequences
============

Rather than having both python and yaml override files for our dev and test
environments, we will move towards having all settings defined in a yaml file
and for all environments to use production.py to load their settings.
