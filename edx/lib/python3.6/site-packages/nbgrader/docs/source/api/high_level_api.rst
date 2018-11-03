High-Level API
==============

.. currentmodule:: nbgrader.apps.api

.. versionadded:: 0.5.0

This API is a high-level api that provides access to nbgrader's core
functionality, for example assigning, releasing, collecting, and autograding
assignments. For example:

.. code:: python

    from nbgrader.apps import NbGraderAPI
    from traitlets.config import Config

    # create a custom config object to specify options for nbgrader
    config = Config()
    config.Exchange.course_id = "course101"

    api = NbGraderAPI(config=config)

    # assuming source/ps1 exists
    api.assign("ps1")

For details on how to configure the API, see :doc:`/configuration/config_options`.

.. autoclass:: NbGraderAPI

    .. automethod:: __init__

    .. autoattribute:: gradebook

    .. automethod:: get_source_assignments

    .. automethod:: get_released_assignments

    .. automethod:: get_submitted_students

    .. automethod:: get_submitted_timestamp

    .. automethod:: get_autograded_students

    .. automethod:: get_assignment

    .. automethod:: get_assignments

    .. automethod:: get_notebooks

    .. automethod:: get_submission

    .. automethod:: get_submissions

    .. automethod:: get_notebook_submission_indices

    .. automethod:: get_notebook_submissions

    .. automethod:: get_student

    .. automethod:: get_students

    .. automethod:: get_student_submissions

    .. automethod:: get_student_notebook_submissions

    .. automethod:: assign

    .. automethod:: release

    .. automethod:: unrelease

    .. automethod:: collect

    .. automethod:: autograde
