##############
Course Grading
##############
This document is written to help professors understand how a final grade for a
course is computed.

Course grading is the process of taking all of the problems scores for a student
in a course and generating a final score (and corresponding letter grade). This 
grading process can be split into two phases - totaling sections and section 
weighting.

*****************
Totaling sections
*****************
The process of totaling sections is to get a percentage score (between 0.0 and
1.0) for every section in the course. A section is any module that is a direct
child of a chapter. For example, psets, labs, and sequences are all common
sections. Only the *percentage* on the section will be available to compute the
final grade, *not* the final number of points earned / possible.

.. important::
  For a section to be included in the final grade, the policies file must set
  `graded = True` for the section.

For each section, the grading function retrieves all problems within the
section. The section percentage is computed as (total points earned) / (total
points possible).

******************
Weighting Problems
******************
In some cases, one might want to give weights to problems within a section. For
example, a final exam might contain four questions each worth 1 point by default.
This means each question would by default have the same weight. If one wanted
the first problem to be worth 50% of the final exam, the policy file could specify
weights of 30, 10, 10, and 10 to the four problems, respectively.

Note that the default weight of a problem **is not 1**. The default weight of a
problem is the module's `max_grade`.

If weighting is set, each problem is worth the number of points assigned, regardless of the number of responses it contains.

Consider a Homework section that contains two problems.

.. code-block:: xml

    <problem display_name=”Problem 1”>
      <numericalresponse> ... </numericalreponse>
    </problem>

.. code-block:: xml

    <problem display_name=”Problem 2”>
      <numericalresponse> ... </numericalreponse>
      <numericalresponse> ... </numericalreponse>
      <numericalresponse> ... </numericalreponse>
    </problem>

Without weighting, Problem 1 is worth 25% of the assignment, and Problem 2 is worth 75% of the assignment.

Weighting for the problems can be set in the policy.json file.

.. code-block:: json

    "problem/problem1": {
      "weight": 2
    },
    "problem/problem2": {
      "weight": 2
    },

With the above weighting, Problems 1 and 2 are each worth 50% of the assignment.

Please note: When problems have weight, the point value is automatically included in the display name *except* when `"weight": 1`. When the weight is 1, no visual change occurs in the display name, leaving the point value open to interpretation to the student.


******************
Weighting Sections
******************
Once each section has a percentage score, we must total those sections into a
final grade. Of course, not every section has equal weight in the final grade.
The policies for weighting sections into a final grade are specified in the
grading_policy.json file.

The `grading_policy.json` file specifies several sub-graders that are each given
a weight and factored into the final grade. There are currently two types of
sub-graders, section format graders and single section graders.

We will use this simple example of a grader with one section format grader and
one single section grader.

.. code-block:: json

    "GRADER" : [
        {
          "type" : "Homework",
          "min_count" : 12,
          "drop_count" : 2,
          "short_label" : "HW",
          "weight" : 0.4
        },
        {
          "type" : "Final",
          "name" : "Final Exam",
          "short_label" : "Final",
          "weight" : 0.6
        }
    ]

Section Format Graders
======================
A section format grader grades a set of sections with the same format, as
defined in the course policy file. To make a vertical named Homework1 be graded
by the Homework section format grader, the following definition would be in the
course policy file.

.. code-block:: json

    "vertical/Homework1": {
        "display_name": "Homework 1", 
        "graded": true, 
        "format": "Homework"
    },


In the example above, the section format grader declares that it will expect to
find at least 12 sections with the format "Homework". It will drop the lowest 2.
All of the homework assignments will have equal weight, relative to each other 
(except, of course, for the assignments that are dropped).

This format supports forecasting the number of homework assignments. For
example, if the course only has 3 homeworks written, but the section format
grader has been told to expect 12, the missing 9 will have an assumed 0% and
will still show up in the grade breakdown.

A section format grader will also show the average of that section in the grade
breakdown (shown on the Progress page, gradebook, etc.).


Single Section Graders
======================
A single section grader grades exactly that - a single section. If a section
is found with a matching format and display name then the score of that section
is used. If not, a score of 0% is assumed.


Combining sub-graders
=====================
The final grade is computed by taking the score and weight of each sub grader.
In the above example, homework will be 40% of the final grade. The final exam
will be 60% of the final grade.

**************************
Displaying the final grade
**************************
The final grade is then rounded up to the nearest percentage point. This is so
the system can consistently display a percentage without worrying whether the
displayed percentage has been rounded up or down (potentially misleading the
student). The formula for the rounding is::

    rounded_percent = round(computed_percent * 100 + 0.05) / 100

The grading policy file also specifies the cutoffs for the grade levels. A
grade is either A, B, or C. If the student does not reach the cutoff threshold
for a C grade then the student has not earned a grade and will not be eligible
for a certificate. Letter grades are only awarded to students who have
completed the course. There is no notion of a failing letter grade.




