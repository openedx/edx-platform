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
The structure of these files try to match `OEP-45` as bast as we can. Because
the edx-platform houses both the ``LMS`` and ``Studio`` applications, our
implementation will differ slightly from the guidance provided by `OEP-45`.

LMS and CMS settings will continue to live under ``lms/envs/...`` and ``cms/envs/...``.

Underneath those folders, we will follow the layout suggested by `OEP-45`.


To recap that here:

``__init__.py`` will handle the loading of defaults, environment overrides, and ensuring that required settings are set.

``defaults.py`` will house and document all default settings.

``required.py`` will document and validate that required settings have been defined.

For edx-platform there may be cases where settings are additive, in this case
the managing of those additive settings will be managed within
``__init__.py``

For example, FEATURES, or JWT_AUTH are both settings where we
currently pull parts of the data from the config and inject it into an existing
data structure. While it is possible that in the future we would make these be
more explicit, we don't want to take on that work now as it may increase
complexity.


.. _OEP-45: https://github.com/edx/open-edx-proposals/pull/143/files

Consequences
============

Rather than having both python and yaml override files for our dev and test
environments, we will move towards having all settings defined in a yaml file
and for all environments to use __init__.py to load their settings.

The following files should be obviated by this change:

* bok_choy_docker.py
* bok_choy.py
* devstack_docker.py
* devstack_optimized.py
* devstack.py
* devstack_with_worker.py
* load_test.py
* openstack.py
* static.py
* test.py
* test_static_optimized.py

If there exist default YAML files for any of the above environments they should
be updated to absorb any overrides that lived in these python settings files.
Any environments that use these files should be updated.

Alternatives Considered
=======================

Don't use YAML files, just python modules
-----------------------------------------

Instead of having YAML and then translating that to python, we can just have
python settings files for all variants we want.

Pros:

* Settings can still be in a single place per environment.
* You get the full power of python when building out settings.
* Settings values can be complex python objects.

Cons:
* Because settings have secrets, we would have to keep our settings file out of
  the public repository.
* This wouldn't solve the problem where we would still try to "inherit" from other settings files and make it harder to read the current value of any given setting.

This alternative gives us a lot more power but it's power that we don't actually need.  Building limitiations into what settings can be helps us keep them simple and understandable.
