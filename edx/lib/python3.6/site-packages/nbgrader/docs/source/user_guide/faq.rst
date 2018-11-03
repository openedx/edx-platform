Frequently asked questions
==========================

.. contents:: Table of contents
   :depth: 2

Can I use nbgrader for purely manually graded assignments (i.e., without autograding)?
--------------------------------------------------------------------------------------------

Yes, absolutely! Mark all the cells where students write their answers as
:ref:`manually-graded-cells` and then during grading run ``nbgrader autograde``
and the formgrader as normal. If you don't want to even execute the
notebooks, you can pass the ``--no-execute`` flag to
:doc:`/command_line_tools/nbgrader-autograde`.

Can I hide the test cells in a nbgrader assignment?
---------------------------------------------------

Yes, as of version 0.5.0 of ``nbgrader`` you will be able to hide tests
in "Autograder tests" cells (see :ref:`autograder-tests-cell-hidden-tests`).

How does nbgrader ensure that students do not change the tests?
---------------------------------------------------------------

Please see the documentation on :ref:`read-only-cells`.

Does nbgrader support parallel autograding of assignments?
----------------------------------------------------------

Not yet, though it is on the todo list (see `#174
<https://github.com/jupyter/nbgrader/issues/174>`_). :ref:`PRs welcome!
<pull-request>`

Does nbgrader protect against infinite loops?
---------------------------------------------

Yes. nbgrader will stop executing a cell after a certain period of time. This
timeout is customizable through the ``ExecutePreprocessor.timeout``
configuration option. See :doc:`/configuration/config_options`.

Does nbgrader protect against unsafe code?
-------------------------------------------

Not yet, though it is on the todo list (see `#483
<https://github.com/jupyter/nbgrader/issues/483>`_). :ref:`PRs welcome!
<pull-request>`

How does nbgrader handle late assignments?
------------------------------------------

By default nbgrader won't explicitly assign late penalties, but it will
compute how late each submission is. If you wish to customize this default
behavior see :doc:`adding customization plugins </plugins/index>`.

For this to work, you must include a duedate for the assignment and then a
``timestamp.txt`` file in the folder for each submission with a single line
containing a timestamp (e.g. ``2015-02-02 14:58:23.948203 PST``). Then, when
you run ``nbgrader autograde``, nbgrader will record these timestamps into the
database. You can access the timestamps through the API, like so:

.. code:: python

    from nbgrader.api import Gradebook
    with Gradebook("sqlite:///gradebook.db") gb:
        assignment = gb.find_assignment("ps1")
        for submission in assignment.submissions:
            print("Submission from '{}' is {} seconds late".format(
                submission.student_id, submission.total_seconds_late))

Note that if you use the release/fetch/submit/collect commands (see
:doc:`managing_assignment_files`), the ``timestamp.txt`` files will be included
automatically.

Do I have to use sqlite for the nbgrader database?
--------------------------------------------------

No, and in fact, if you have multiple people grading accessing the formgrader
at the same time we strongly encourage you **not** to use sqlite because it is
not threadsafe. Postgres is also supported, and anything else that works with
SQLAlchemy is likely to work (e.g. MySQL), though only sqlite and Postgres have
been tested. If you want to use another SQL-based database and find that it
doesn't work for some reason, please `open an issue
<https://github.com/jupyter/nbgrader/issues/new>`_!

Does nbgrader work with non-Python kernels?
-------------------------------------------

Yes, though it hasn't been extensively tested with other kernels and it is
likely there are some edge cases where things do not work quite right. One
thing in particular that you will need to do is :doc:`customize how the
student version </configuration/student_version>` is produced -- for example,
you will need to change the delimiters for the solution regions to use the
appropriate comment marks for your language.

If you run into any issues using nbgrader with other kernels, please `open an
issue <https://github.com/jupyter/nbgrader/issues/new>`_!

How do I get out grade information from the database?
-----------------------------------------------------

nbgrader offers a fairly rich :doc:`API </api/index>` for interfacing with the
database. Please see :ref:`getting-information-from-db` for more details.

.. _multiple-classes:

Can I use the "Assignment List" extension with multiple classes?
----------------------------------------------------------------

Yes, though support for this is currently minimal. To use the "Assignment List"
extension in multiple courses, you will want to set the following config option
in your students' ``nbgrader_config.py`` files:

.. code:: python

    c = get_config()
    c.Exchange.path_includes_course = True

This will tell the transfer apps (i.e. ``nbgrader fetch``, ``nbgrader submit``,
and ``nbgrader list``) to assume that the paths for assignments include the
course name, such as ``./course101/ps1`` rather than just ``./ps1`` (which is
the default).

Then, when using the "Assignment List" extension, students will be able to
switch between different classes. However, there is no support currently for
access control: all students will be able to see all assignments from all
classes (unless you specifically set the ``course_id`` in the config file, in
which case they will only be able to see assignments for that specific course).
See `#544 <https://github.com/jupyter/nbgrader/issues/544>`_ for details.
:ref:`PRs welcome! <pull-request>`

Is nbgrader compatible with Windows/Mac/Linux?
----------------------------------------------

Linux and Mac
~~~~~~~~~~~~~

nbgrader is fully compatible with Linux and also with Mac (with the exception
of JupyterHub integration, as JupyterHub does not run on Mac).

Windows
~~~~~~~

The core pieces of nbgrader will also work on Windows: the "Create Assignment"
extension, ``nbgrader assign``, ``nbgrader autograde``, ``nbgrader formgrade``,
``nbgrader feedback``, ``nbgrader validate``, and ``nbgrader export``.

However, the parts of nbgrader corresponding to file management (the
"Assignment List" extension, ``nbgrader release``, ``nbgrader fetch``,
``nbgrader submit``, ``nbgrader collect``, ``nbgrader list``) will *not* work
under Windows.

What happens if I do some manual grading, and then rerun the autograder?
------------------------------------------------------------------------

If you rerun the autograder, nbgrader will never overwrite any manual grades or
comments that you have added, and manual grades *always* take precedence over
autogrades.

However, if you have given a manual grade, then rerun the autograder, and the
autograder produces a grade as well, then it will mark that problem as "needing
manual grade". This functionality is primarily to aid you in grading in the
scenarios where you want to grade a newer version of the student's
submission—for example, if you gave them a chance to revise it. In this
hypothetical scenario, a student might have not completed a problem, leading
you to originally assign it a low partial credit score. But then they turn in a
newer version, which you run through the autograder and which attains full
credit. Since the manual grade always takes precedence over the autograde, the
student would still receive the low score unless you updated your grade: hence
the motivation for marking it as needing to be manually graded (again).

Do students have to install anything on their own computers to use nbgrader?
----------------------------------------------------------------------------
No, nbgrader only needs to be installed for the instructor. However, students
may optionally install the Validate extension to verify that their submission
passes all the test cases.

Can tests be only temporarily hidden, so that students can reveal them?
-----------------------------------------------------------------------
No, the tests are either present in the student version of the notebook or they
are not. However, there exist extensions such as
https://github.com/kirbs-/hide_code which can assist in hiding code cells.
