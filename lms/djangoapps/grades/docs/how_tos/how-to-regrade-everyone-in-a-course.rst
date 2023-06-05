How to Update Grades for Every Learner in a Course
--------------------------------------------------

This will help if you want to re-computer the persistent subsection and course
grades for every learner in a course.
**If grades for your course are currently frozen, you must first complete the "What to do if grades are frozen" section below.**

Steps to trigger course-wide re-grade
=====================================

1. Go to LMS Django Admin and add an entry in ComputeGradesSetting, in the Grades section. 
   ``/admin/grades/computegradessetting/``
   (this requires the persistent_grades_admin role in app-permissions)

2. Put the course key of the course you wish to recompute into the ``course ids`` field.
   You can enter multiple whitespace-separated keys. Save the model.

3. Go to tools-edx-jenkins and navigate to Grading/(prod,stage)-edx-compute_grades
   You must be a member of the jenkins-tools-grading-jobs github group to run the job, or you can ask a member to run the job for you.

4. The job will grab the most recent ComputeGradesSetting model and enqueue a task to recompute course grades for
   the course(s) you specified in step 2.

What to do if grades are frozen
===============================

By default, we don't allow for subsection or course grades to be changed after
30 days from the end date of a course have elapsed.  If the course you want to
update grades for currently has "frozen" grades, you need to do the following:

1. Go to the Django Admin page and find the "Waffle flag course overrides" page, for example
   https://courses-internal.stage.edx.org/admin/waffle_utils/waffleflagcourseoverridemodel/

2. Ensure that there is not currently an entry with the flag name
   ``grades.enforce_freeze_grade_after_course_end`` for this course.

3. Click the "Add Waffle Flag Course Override" button.

4. Enter the flag name from step (2) in the "Waffle flag" field.

5. Enter the course id of the course.

6. Select "Force Off" for the "Override choice" field.

7. Check the "Enabled" checkbox.

8. Click "Save"

9. Exit the Django Admin site and proceed to the section above.

Monitoring
==========

You should be able to track the progress of the re-grade by searching
for your course id and the ``compute_all_grades_for_course`` task name in Splunk.
Initially, that task will have been received, but not started.  When it does start,
you'll see a bunch of child tasks like ``recalculate_course_and_subsection_grades_for_user``
that indicate grades are being re-calculated for the learners in this course.
