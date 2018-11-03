Using nbgrader with JupyterHub
==============================

.. seealso::

    :doc:`/user_guide/creating_and_grading_assignments`
        Documentation for ``nbgrader assign``, ``nbgrader autograde``, ``nbgrader formgrade``, and ``nbgrader feedback``.

    :doc:`/user_guide/managing_assignment_files`
        Documentation for ``nbgrader release``, ``nbgrader fetch``, ``nbgrader submit``, and ``nbgrader collect``.

    :doc:`config_options`
        Details on ``nbgrader_config.py``

    :doc:`/user_guide/philosophy`
        More details on how the nbgrader hierarchy is structured.

    `JupyterHub Documentation <https://jupyterhub.readthedocs.io/en/latest/getting-started/index.html>`_
        Detailed documentation describing how JupyterHub works, which is very
        much required reading if you want to integrate the formgrader with
        JupyterHub.

For instructors running a class with JupyterHub, nbgrader offers several tools
that optimize and enrich the instructors' and students' experience of sharing
the same system. By integrating with JupyterHub, nbgrader streamlines the
process of releasing and collecting assignments for the instructor and of
fetching and submitting assignments for the student. In addition to using the
``nbgrader release``, ``nbgrader fetch``, ``nbgrader submit``, and ``nbgrader
collect`` commands (see :doc:`/user_guide/managing_assignment_files`) with a
shared server setup like JupyterHub, the formgrader (see
:doc:`/user_guide/creating_and_grading_assignments`) can be configured to
integrate with JupyterHub so that all grading can occur on the same server.

.. warning::

    The way that the formgrader integrates with JupyterHub changed between
    versions 0.4 and 0.5 in a backwards-incompatible way. However, this means
    that the formgrader should be trivially easy to use with JupyterHub!

Starting in version 0.5.0 of nbgrader, the formgrader is no longer a standalone
command. Rather, it is an extension of the Jupyter notebook. This means that
the formgrader will work out-of-the-box with JupyterHub if you only have a
single grader for your class: all you need to do is make sure that you have
installed and enabled the nbgrader extensions (see
:doc:`/user_guide/installation`) and then make sure the path to your course
directory is properly set in ``~/.jupyter/nbgrader_config.py``:

.. code:: python

    c = get_config()
    c.CourseDirectory.root = 'path/to/course/files'

If you have multiple graders, then you can set up a `shared notebook server
<https://github.com/jupyterhub/jupyterhub/tree/master/examples/service-notebook>`_
as a JupyterHub service. As before, you will need to ensure that the nbgrader
extensions are installed and enabled, and then you will need to make sure the
shared notebook server has access to an ``nbgrader_config.py`` which points to
the correct course directory.
