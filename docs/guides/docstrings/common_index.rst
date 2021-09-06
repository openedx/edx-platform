common
******

The ``common`` directory in edx-platform is home to an assortment of packages
used by the LMS and Studio.  This is a legacy code organization decision, and
it is currently intended that most of the code here will eventually either be
moved into the ``openedx`` package or broken out into a separately installed
package.

.. toctree::
    :maxdepth: 2

    common_djangoapps
    common_lib
