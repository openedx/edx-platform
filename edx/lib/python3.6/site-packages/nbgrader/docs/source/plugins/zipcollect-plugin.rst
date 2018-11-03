ZipCollect plugins
==================

.. versionadded:: 0.5.0

Extractor plugin
----------------

Extract archive (zip) files in the `archive_directory`. Archive files are
extracted to the `extracted_directory`. Non-archive (zip) files found in the
`archive_directory` are copied to the `extracted_directory`. Archive files will
be extracted into their own sub-directory within the `extracted_directory` and
any archive files within archives will also be extracted into their own
sub-directory along the path.

Creating a plugin
^^^^^^^^^^^^^^^^^

To add your own extractor you can create a plugin class that inherits from
:class:`~nbgrader.plugins.zipcollect.ExtractorPlugin`. This class needs to only
implement one method, which is the
:func:`~nbgrader.plugins..zipcollect.ExtractorPlugin.extract` method (see
below). Let's say you create your own plugin in the ``myextractor.py`` file,
and your plugin is called ``MyExtractor``. Then, on the command line, you would
run::

    nbgrader zip_collect --extractor=myextractor.MyExtractor

which will use your custom extractor rather than the built-in one.

API
^^^

.. currentmodule:: nbgrader.plugins.zipcollect

.. autoclass:: ExtractorPlugin

    .. automethod:: extract


FileNameCollector plugin
------------------------

Apply a named group regular expression to each filename received from the
:class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` and return ``None`` if the
file should be skipped or a dictionary that, at the very least, contains the
``student_id`` and ``file_id`` key value pairs; and optionally contains the
``timestamp`` key value pair, for example:

.. code:: python

    dict(
        file_id='problem1.ipynb',
        student_id='hacker',
        timestamp='2017-01-30 15:30:10 UCT'
    )

For more information about named group regular expressions see
`<https://docs.python.org/howto/regex.html>`_

Note: ``file_id`` must contain the relative path to the assignment when
collecting submission files in assignment sub-folders, for example:

.. code:: python

    dict(
        file_id='data/sample.txt',
        student_id='hacker',
        timestamp='2017-01-30 15:30:10 UCT'
    )


Creating a plugin
^^^^^^^^^^^^^^^^^

To add your own collector you can create a plugin class that inherits from
:class:`~nbgrader.plugins.zipcollect.FileNameCollectorPlugin`. This class needs
to only implement one method, which is the
:func:`~nbgrader.plugins..zipcollect.FileNameCollectorPlugin.collect` method
(see below). Let's say you create your own plugin in the ``mycollector.py``
file, and your plugin is called ``MyCollector``. Then, on the command line, you
would run::

    nbgrader zip_collect --collector=mycollector.MyCollector

which will use your custom collector rather than the built-in one.

API
^^^

.. currentmodule:: nbgrader.plugins.zipcollect

.. autoclass:: FileNameCollectorPlugin

    .. automethod:: collect
