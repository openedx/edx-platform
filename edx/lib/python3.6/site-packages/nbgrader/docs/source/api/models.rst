Database models
===============

.. currentmodule:: nbgrader.api

In general, these database models should **never** be modified by hand. You should
only ever modify them using a :class:`~nbgrader.api.Gradebook` object, so that
changes are properly persisted to the database, and so that the models don't end
up in an inconsistent state. However, some methods of the :class:`~nbgrader.api.Gradebook`
object return database model objects, so those models and their attributes are
documented here for reference.

.. autoclass:: Student

    .. autoattribute:: id

    .. autoattribute:: first_name

    .. autoattribute:: last_name

    .. autoattribute:: email

    .. autoattribute:: score

    .. autoattribute:: max_score

    .. autoattribute:: submissions

    .. automethod:: to_dict

Master version of an assignment
-------------------------------

.. autoclass:: Assignment

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: duedate

    .. autoattribute:: notebooks

    .. autoattribute:: submissions

    .. autoattribute:: num_submissions

    .. autoattribute:: max_score

    .. autoattribute:: max_code_score

    .. autoattribute:: max_written_score

    .. automethod:: to_dict

.. autoclass:: Notebook

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: assignment
        :annotation:

    .. autoattribute:: assignment_id

    .. autoattribute:: grade_cells

    .. autoattribute:: solution_cells

    .. autoattribute:: source_cells

    .. autoattribute:: submissions

    .. autoattribute:: num_submissions

    .. autoattribute:: max_score

    .. autoattribute:: max_code_score

    .. autoattribute:: max_written_score

    .. autoattribute:: needs_manual_grade

    .. autoattribute:: kernelspec

    .. automethod:: to_dict

.. autoclass:: GradeCell

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: max_score

    .. autoattribute:: cell_type

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: assignment

    .. autoattribute:: grades

    .. automethod:: to_dict

.. autoclass:: SolutionCell

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: assignment

    .. autoattribute:: comments

    .. automethod:: to_dict

.. autoclass:: SourceCell

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: cell_type

    .. autoattribute:: source

    .. autoattribute:: checksum

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: assignment

    .. automethod:: to_dict


Submitted assignments
---------------------

.. autoclass:: SubmittedAssignment

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: assignment
        :annotation:

    .. autoattribute:: assignment_id

    .. autoattribute:: student
        :annotation:

    .. autoattribute:: student_id

    .. autoattribute:: timestamp

    .. autoattribute:: extension

    .. autoattribute:: duedate

    .. autoattribute:: total_seconds_late

    .. autoattribute:: notebooks

    .. autoattribute:: score

    .. autoattribute:: max_score

    .. autoattribute:: code_score

    .. autoattribute:: max_code_score

    .. autoattribute:: written_score

    .. autoattribute:: max_written_score

    .. autoattribute:: needs_manual_grade

    .. automethod:: to_dict

.. autoclass:: SubmittedNotebook

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: assignment
        :annotation:

    .. autoattribute:: assignment_id

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: grades

    .. autoattribute:: comments

    .. autoattribute:: student

    .. autoattribute:: flagged

    .. autoattribute:: score

    .. autoattribute:: max_score

    .. autoattribute:: code_score

    .. autoattribute:: max_code_score

    .. autoattribute:: written_score

    .. autoattribute:: max_written_score

    .. autoattribute:: needs_manual_grade

    .. autoattribute:: failed_tests

    .. autoattribute:: late_submission_penalty

.. autoclass:: Grade

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: assignment

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: cell
        :annotation:

    .. autoattribute:: cell_id

    .. autoattribute:: cell_type

    .. autoattribute:: student

    .. autoattribute:: auto_score

    .. autoattribute:: manual_score

    .. autoattribute:: extra_credit

    .. autoattribute:: score

    .. autoattribute:: max_score

    .. autoattribute:: needs_manual_grade

    .. autoattribute:: failed_tests

    .. automethod:: to_dict

.. autoclass:: Comment

    .. autoattribute:: id

    .. autoattribute:: name

    .. autoattribute:: assignment

    .. autoattribute:: notebook
        :annotation:

    .. autoattribute:: notebook_id

    .. autoattribute:: cell
        :annotation:

    .. autoattribute:: cell_id

    .. autoattribute:: student

    .. autoattribute:: auto_comment

    .. autoattribute:: manual_comment

    .. autoattribute:: comment

    .. automethod:: to_dict
