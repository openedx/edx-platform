How to Update Grades for Every Learner in a Course
--------------------------------------------------

This will help if you want to re-computer the persistent subsection and course
grades for every learner in a course.
**If grades for your course are currently frozen, you must first complete the "What to do if grades are frozen" section below.**

Steps to trigger course-wide re-grade
=====================================

1. Go to the Studio grading settings for the course,
   for example https://studio.stage.edx.org/settings/grading/edX/DemoX/Demo_Course .

2. Make a trivial edit to one of the assignment type names.  For example,
   for an assignment type named "Homework", add a space to get "Homework ",
   and then delete the space.

3. Studio should now alert you that you've made changes;
   click the "Save Changes" button at the bottom of your screen.

4. Changing the grading policy of the course (even though you made no change of consequence)
   will cause an asynchronous task called ``compute_all_grades_for_course`` to be enqueued.
   This task re-computes grades for every graded subsection in the course, for every learner
   in the course.  This will also cause course grades to be re-computed for
   every learner in the course.  Note that, for the purpose of "throttling",
   **there's a 1 hour delay between the enqueueing of this task and the actual
   re-computation of grades.**

5. Exit Studio.

6. Ask an engineer to help you with the "Monitoring" section below.

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
