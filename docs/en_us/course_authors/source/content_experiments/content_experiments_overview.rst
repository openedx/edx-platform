.. _Overview of Content Experiments:

#################################
Overview of Content Experiments
#################################

You use content experiments to show different course content to different
groups of students.

Also known as A/B or split tests, content experiments enable you to
research and compare the performance of students in different groups to gain
insight into the relative effectiveness of your course content.

.. caution::
  If you have graded problems within a content experiment, grade exports do not
  work for your course. This issue is currently being addressed.

For more information, see:

* :ref:`Configure Your Course for Content Experiments`
* :ref:`Add Content Experiments to Your Course`
* :ref:`Test Content Experiments`

.. _Courses with Multiple Content Experiments:

******************************************
Courses with Multiple Content Experiments
******************************************

You can run multiple content experiments in your course. You can set up each
experiment to use the same groups of students, or you can set up each
experiment to be independent and use a different grouping.

.. important::

  If your course has multiple experiments, it is critical that you decide
  up front if the experiments share the same groups of students or if each
  experiment has its own unique grouping. If two experiments share the same
  grouping, then any student that is in Group A for the first experiment will
  also be in Group A for the second one. If you want the experiments to be
  independent, then the experiments must use different groupings so that
  students are randomly assigned for each experiment.

To determine the available groupings of students, you :ref:`set up group
configurations in Studio <Set up Group Configurations in edX Studio>` or
:ref:`in XML <Set up Group Configurations in an XML Course>`.

You then select which grouping to use when you :ref:`add a content experiment
in Studio <Add a Content Experiment in Studio>` or :ref:`in XML <Add a Content
Experiment in XML>`.