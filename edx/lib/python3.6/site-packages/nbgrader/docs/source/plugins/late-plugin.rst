Late submission plugin
======================

Assigning a penalty to notebooks that were submitted late can be done using the
method described below. The default behavior is not to assign any penalty.
nbgrader will still compute how late each submission is.

For this to work, you must include a duedate for the assignment and then a
``timestamp.txt`` file in the folder for each submission with a single line
containing a timestamp (e.g. ``2015-02-02 14:58:23.948203 PST``).
Then, when you run ``nbgrader autograde``, nbgrader will record these
timestamps into the database, compute how late each submission is and assign a
late penalty (if specified). Also see the :doc:`faq </user_guide/faq>`.


Predefined methods
------------------

To assign an overall notebook score of zero for any late submission you can
include the following in the ``{course_directory}/nbgrader_config.py`` file::

    c.LateSubmissionPlugin.penalty_method = 'zero'


Creating a plugin:
------------------

To add your own custom management of late submissions you can create a plugin
class. For example the ``{course_directory}/late.py`` module that
assigns a penalty of 1 point per hour late:::

    from __future__ import division
    from nbgrader.plugins import BasePlugin


    class SubMarks(BasePlugin):
        def late_submission_penalty(student_id, score, total_seconds_late):
            """Penalty of 1 mark per hour late"""
            hours_late = total_seconds_late / 3600
            return round(hours_late, 0)


The class must inherit from ``BasePlugin`` and the ``late_submission_penalty``
function API is described below. The module and class names are arbitrary, but
need to be added to the ``{course_directory}/nbgrader_config.py`` file, for
example:::

    c.AssignLatePenalties.plugin_class = 'late.SubMarks'


Note: the ``late.py`` module can be either located in the same
directory as where you are running the nbgrader commands (which is most
likely the root of your course directory), or you can place it in one of
a number of locations on your system. These locations correspond to the
configuration directories that Jupyter itself looks in; you can find out
what these are by running ``jupyter --paths``.


API
---

.. currentmodule:: nbgrader.plugins.latesubmission

.. autoclass:: LateSubmissionPlugin

    .. automethod:: late_submission_penalty
