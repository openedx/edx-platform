Export plugin
=============

.. versionadded:: 0.4.0

Many instructors need to be able to get grades for their class out of the
nbgrader database and into another format, such as a CSV file, a learning
management system (LMS) like Canvas or Blackboard, etc. nbgrader comes with the
capability to export grades to a CSV file, however you may want to customize
this functionality for your own needs.

Creating a plugin
-----------------

To add your own grade exporter you can create a plugin class that inherits from
``nbgrader.plugins.ExportPlugin``. This class needs to only implement one
method, which is the :func:`~nbgrader.plugins.export.ExportPlugin.export` method (see
below). Let's say you create your own plugin in the ``myexporter.py`` file, and
your plugin is called ``MyExporter``. Then, on the command line, you would
run::

    nbgrader export --exporter=myexporter.MyExporter

which will use your custom exporter rather than the built-in CSV exporter. For
an example of how to interface with the database, please see
:ref:`getting-information-from-db`.

API
---

.. currentmodule:: nbgrader.plugins.export

.. autoclass:: ExportPlugin

    .. automethod:: export
