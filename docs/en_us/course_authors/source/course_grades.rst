.. _Grades:

############################
Grades
############################

You can review information about how grading is configured for your course, and generate student grades, at any time after you create the course. You can also make adjustments to how a problem is graded, for a single student or all students.

For information about the grading data you can access and the changes you can make, see the following topics:

* :ref:`Review_grades`

* :ref:`Access_grades`

* :ref:`Adjust_grades`

For information about how you establish a grading policy and work with the problem components in your course, see :ref:`Establish a Grading Policy` or :ref:`Working with Problem Components`.

**Important**: If you make changes to your grading policy or problem components after a course starts, students can see the effect of your changes on their Progress pages. Be sure to announce any changes on your Course Info page.

.. _Review_grades:

********************************************************
Review how grading is configured for your course
********************************************************

You can review the assignment types that are graded and their respective weights on the Instructor Dashboard.

You establish a grading policy for your course when you create it in Studio. While the course is running, you can view an XML representation of the assignment types in your course and how they are weighted to determine students' grades.

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download** > **Grading Configuration**.

   A list of the assignment types in your course displays. In this example, Homework is weighted as 60% of the grade. 

   .. image:: Images/Grading_Configuration.png
     :alt: XML of course assignment types and weights for grading

   In Studio, you define this information by selecting **Settings** > **Grading**.

   .. image:: Images/Grading_Configuration_Studio.png
     :alt: Studio example of homework assignment type and grading weight

For more information, see :ref:`configure`.


.. _Access_grades:

********************************************************
Access student grades
********************************************************

You can generate and review your students' grades at any time during your course. You can generate grades for all currently enrolled students, or check the progress of a single student, who can be enrolled or unenrolled.

=========================================================
Generate grades for enrolled students
=========================================================

When you initiate calculations to grade student work, a process starts on the edX servers. The complexity of your grading configuration and the number of students enrolled in your course affect how long this process takes. You can download the calculated grades in a CSV (comma-separated values) file when the grading process is complete. You cannot view student grades on the Instructor Dashboard. 

To generate grades for the students who are currently enrolled in your course:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download**.

#. To start the grading process, click **Generate Grade Report**.

A status message indicates that the grading process is in progress. This process can take some time to complete, but you can navigate away from this page and do other work while it runs.

When the file is ready for download, a link to the CSV file displays at the bottom of this page.

==========================================
Download grades for enrolled students
==========================================

After you request a grade report for your students, the result is a time-stamped CSV file that includes columns to identify each student: id, email, and username. It also includes a column for every assignment that is included in your grading configuration: each homework, lab, midterm, final, and any other assignment type you added to your course. 

To download a file of student grades:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download**.

#. To open or save a grade report file, click the *course_id* \_grade_report_\ *date*.csv file name at the bottom of the page.

**Note**: To prevent the accidental distribution of student data, you can only download these files by clicking the links on this page. You cannot copy a link and save it or email it, as the value for the link that you copy expires within five minutes.

=========================================================
Check the progress of a single student
=========================================================

For a single student, you can review a chart that plots the grade earned for every graded assignment, and the overall total, as of the current date. You identify the student by supplying either an email address or username. 

Students can view a similar chart (of their own progress only) when they are logged in to the course.

To view current grades for a student:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**.

#. In the Student-Specific Grade Inspection section, enter the student's email address or username.

#. Click **Student Progress Page**.

The Course Progress page for the student displays a chart with the grade for each homework, lab, midterm, final, and any other assignment types in your course, and the total grade earned for the course to date. 

   .. image:: Images/Student_Progress.png
     :alt: A bar chart from a student's Progress page showing grade acheived for each assignment

=========================================================
Check a student's submission and submission history
=========================================================

For a single student and problem, you can review the exact response submitted, the number of attempts made, and the date and time of the submission. You identify the student by supplying a username. 

To review a response submitted by a student:

#. View the live version of your course.

#. Click **Courseware** and navigate to the component that contains the problem you want to review.

#. Display the problem then click **Submission history** at the end of the page.

#. Enter the username for the student whose work you want to review and click **View History** at the end of the page.

Information about the response or responses provided by the student displays. 

To close the Submission History Viewer, click on the browser page outside of the viewer.

===================================================
View a histogram of scores for a problem
===================================================

You can view a chart of the score distribution for a specified problem.

**Note**: In order to view the score distribution for a problem, you need its unique identifier. See :ref:`find_URL`.

To display demographic distributions for gender and educational attainment:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Analytics**. 

#. In the Grade Distribution section, select a problem by using its URL. 

   A graph displays a histogram of scores for that problem.

..  **Question**: (sent to Olga 31 Jan 14) this is a tough UI to use: how do they correlate the codes in this drop-down with actual constructed problems? the copy-and-paste UI on the Student Admin page actually works a little better imo.
.. **Question**: I'd like to include an image, but need a good example. Elina suggested using the edX demo course (I don't have access), and a problem that has multiple possible answers

.. _Adjust_grades:

***********************************
Adjust grades
***********************************

You can adjust grades for one student at a time, or for all of the enrolled students in the course. For example, your course beta testers can evaluate numerous different correct and incorrect responses to verify that your course is set up as you intend. Students can also report problems while a course is running. 

When an error is discovered or corrected, or if you modify a problem after students or beta testers have attempted to answer it, you can either:

* Rescore the submitted answers to reevaluate the work.

* Reset the number of attempts made to answer the question correctly so that students can try again.

To make these adjustments, you need to specify a problem by supplying the unique identifier from its URL.

.. _find_URL:

==================================================
Find the URL for a problem
==================================================

When you create each of the problems for a course, edX assigns a unique identifier. To make grading adjustments for a problem, or to view data about it, you need to specify this identifier.

To find the unique identifier in the URL for a problem:

#. View the live version of your course.

#. Click **Courseware** and navigate to the component that contains the problem you want to review.

#. Display the problem, and click **Staff Debug Info**.

   Information about the problem displays, including its location or URL. This URL ends with the type of module, which is typically "problem", and the unique identifier. 

   .. image:: Images/Problem_URL.png
    :alt: The Staff Debug view of a problem with the unique identifier indicated at the end of a URL address


#. To copy the identifier that is assigned to the problem, select it, right click, and choose **Copy**.

   **Note**: If the URL does not include "problem/" before the identifer, you will need to specify that module identifier as well. Select and copy both the module identifer and the problem identifier.

   To close the Staff Debug viewer, click on the browser page outside of the viewer.

===================================================
Rescore student submissions
===================================================

Each problem that you define for your course includes a correct answer, and may also include a tolerance or acceptable alternatives. If you decide to make a change to these values, you can recore any responses that were already submitted. For a specified problem, you can rescore the work submitted by a single student, or rescore the submissions made by every enrolled student. 

**Note:** You can only rescore problems that have a correct answer entered in edX Studio. Problems that are scored by an external grader cannot be rescored with this procedure.

In order to rescore a problem, you need its unique identifier. See :ref:`find_URL`.

To rescore a problem:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**. 

#. To recore a problem for one student, you work in the Student-Specific Grade Adjustment section of the page. Enter the student's email address or username and the problem URL then click **Rescore Student Submission**.

#. To rescore a problem for all enrolled students, you work in the Course-Specific Grade Adjustment section of the page. Enter the problem URL then click **Rescore ALL students' problem submissions**. 

#. A dialog opens to indicate that the rescore process is in progress. Click **OK**. 

   This process does not take long for a single student, but can take some time to complete for all enrolled students. The process runs in the background, so you can navigate away from this page and do other work while it runs.

#. To view the results of the rescore process, click either **Show Background Task History for Student** or **Show Background Task History for Problem**.

   A table displays the status of the rescore process for each student or problem.

===================================================
Reset student attempts
===================================================

When you create a problem, you can limit the number of times that a student can try to answer that problem correctly. If unexpected issues occur for a problem, you can reset the value for one particular student's attempts back to zero so that the student can begin work over again. If the unexpected behavior affects all of the students in your course, you can reset the number of attempts for all students to zero. 

For more information about modifying a released problem, including other workarounds, see :ref:`Modifying a Released Problem`.

**Note**: In order to reset the number of attempts for a problem, you need its unique identifier. See :ref:`find_URL`.

To reset student attempts for a problem:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**. 

#. To reset the number of attempts for one student, you work in the Student-Specific Grade Adjustment section of the page. Enter the student's email address or username and the problem URL then click **Reset Student Attempts**.

#. To reset the number of attempts for all enrolled students, you work in the Course-Specific Grade Adjustment section of the page. Enter the problem URL then click **Reset ALL students' attempts**. 

#. A dialog opens to indicate that the reset process is in progress. Click **OK**. 

   This process does not take long for a single student, but can take some time to complete for all enrolled students. The process runs in the background, so you can navigate away from this page and do other work while it runs.

#. To view the results of the reset process, click either **Show Background Task History for Student** or **Show Background Task History for Problem**.

   A table displays the status of the reset process for each student or problem.

