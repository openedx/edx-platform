.. _Grades:

############################
Grade and Answer Data
############################

You can review information about how grading is configured for your course, and access student grades, at any time after you create the course. You can also make adjustments to how a problem is graded, for a single student or all students. For information about the grading data that you can access and the changes you can make, see the following topics:

* :ref:`Review_grades`

* :ref:`Access_grades`

* :ref:`Adjust_grades`

To review student answers to the problems in your course, you can download data for course problems or review a graph for a selected problem. See :ref:`Review_Answers`.

For information about how you establish a grading policy and work with the Problem components in your course, see :ref:`Establish a Grading Policy` or :ref:`Working with Problem Components`.

**Important**: If you make changes to your grading policy after a course starts, students can see the effect of your changes on their Progress pages. Be sure to announce any changes on your Course Info page.

.. _Review_grades:

********************************************************
Review How Grading Is Configured for Your Course
********************************************************

You can review the assignment types that are graded and their respective weights on the Instructor Dashboard.

You establish a grading policy for your course when you create it in Studio. While the course is running, you can view an XML representation of the assignment types in your course and how they are weighted to determine students' grades.

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download** > **Grading Configuration**.

   A list of the assignment types in your course displays. In this example, Homework is weighted as 60% of the grade. 

   .. image:: ../Images/Grading_Configuration.png
     :alt: XML of course assignment types and weights for grading

   In Studio, you define this information by selecting **Settings** > **Grading**.

   .. image:: ../Images/Grading_Configuration_Studio.png
     :alt: Studio example of homework assignment type and grading weight

For more information, see :ref:`Configure the Assignment Types`.

.. _Access_grades:

********************************************************
Access Student Grades
********************************************************

You can generate and review your students' grades at any time during your course. You can generate grades for all currently enrolled students, or check the progress of a single student (who can be enrolled or unenrolled).

=========================================================
Generate Grades for Enrolled Students
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
Download Grades for Enrolled Students
==========================================

After you request a grade report for your students, the result is a time-stamped CSV file that includes columns to identify each student: id, email, and username. It also includes a column for every assignment that is included in your grading configuration: each homework, lab, midterm, final, and any other assignment type you added to your course. 

To download a file of student grades:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download**.

#. To open or save a grade report file, click the ``{course_id}_grade_report_{date}.csv`` file name at the bottom of the page.


.. note:: To prevent the accidental distribution of student data, you can only download these files by clicking the links on this page. Do not copy these links for reuse elsewhere, as they expire within 5 minutes. The links on this page also expire if the page is open for more than 5 minutes: if necessary, refresh the page to generate new links. 


=========================================================
Check the Progress of a Single Student
=========================================================

For a single student, you can review a chart that plots the grade earned for every graded assignment, and the overall total, as of the current date. You identify the student by supplying either an email address or username. You can check the progress for students who are currently enrolled in, or who have unenrolled from, the course.

Students can view a similar chart (of their own progress only) when they are logged in to the course.

To view current grades for a student:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**.

#. In the Student-Specific Grade Inspection section, enter the student's email address or username.

#. Click **Student Progress Page**.

The Course Progress page for the student displays a chart with the grade for each homework, lab, midterm, final, and any other assignment types in your course, and the total grade earned for the course to date. 

   .. image:: ../Images/Student_Progress.png
     :alt: A bar chart from a student's Progress page showing grade acheived for each assignment


=========================================================
Check a Student's Submission and Submission History
=========================================================

For a single student and problem, you can review the exact response submitted, the number of attempts made, and the date and time of the submission. You identify the student by supplying a username. 

To review a response submitted by a student:

#. View the live version of your course.

#. Click **Courseware** and navigate to the component that contains the problem you want to review.

#. Display the problem then click **Submission history** at the end of the page.

#. Enter the username for the student whose work you want to review and click **View History** at the end of the page.

Information about the response or responses provided by the student displays. 

To close the Submission History Viewer, click on the browser page outside of the viewer.


.. _Adjust_grades:

***********************************
Adjust Grades
***********************************

You can adjust grades for one student at a time, or for all of the enrolled students in the course. For example, your course beta testers can evaluate numerous different correct and incorrect responses to verify that your course is set up as you intend. Students can also report errors while a course is running. 

When an error is discovered or corrected, or if you decide that you must modify a problem after students or beta testers have attempted to answer it, you can either:

* Rescore the submitted answers to reevaluate the work.

* Reset the number of attempts made to answer the question correctly so that students can try again.

To make these adjustments, you need to specify a problem by supplying the unique identifier from its URL.

.. _find_URL:

==================================================
Find the Unique Identifier for a Problem
==================================================

When you create each of the problems for a course, edX assigns a unique identifier. To make grading adjustments for a problem, or to view data about it, you need to specify this identifier.

To find the unique identifier in the URL for a problem:

#. View the live version of your course.

#. Click **Courseware** and navigate to the component that contains the problem you want to review.

#. Display the problem, and click **Staff Debug Info**.

   Information about the problem displays, including its location or URL. This URL ends with the type of module, which is typically "problem", and the unique identifier. 

   .. image:: ../Images/Problem_URL.png
    :alt: The Staff Debug view of a problem with the unique identifier indicated at the end of a URL address


4. To copy the identifier that is assigned to the problem, select it, right click, and choose **Copy**.


   **Note:** If the URL does not include "problem/" before the identifier, you will need to specify that module identifier as well. Select and copy both the module identifier and the problem identifier.

   To close the Staff Debug viewer, click on the browser page outside of the viewer.

===================================================
Rescore Student Submissions
===================================================

Each problem that you define for your course includes a correct answer, and may also include a tolerance or acceptable alternatives. If you decide to make a change to these values, you can rescore any responses that were already submitted. For a specified problem, you can rescore the work submitted by a single student, or rescore the submissions made by every enrolled student. 

**Note**: You can only rescore problems that have a correct answer entered in edX Studio. Problems that are scored by an external grader cannot be rescored with this procedure.

To rescore a problem, you need its unique identifier. See :ref:`find_URL`.

To rescore a problem:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**. 

#. Rescore the problem, either for an individual student or for all students.

   To rescore a problem for one student, you work in the **Student-Specific Grade Adjustment** section of the page. Enter the student's email address or username and the unique problem identifier, and then click **Rescore Student Submission**.

   To rescore a problem for all enrolled students, you work in the **Course-Specific Grade Adjustment** section of the page. Enter the unique problem identifier, and then click **Rescore ALL students' problem submissions**. 

5. When you see a dialog box that notifies you that the rescore process is in progress, click **OK**. 

   This process does not take long for a single student, but can take some time to complete for all enrolled students. The process runs in the background, so you can navigate away from this page and do other work while it runs.

6. To view the results of the rescore process, click either **Show Background Task History for Student** or **Show Background Task History for Problem**.

   A table displays the status of the rescore process for each student or problem.

===================================================
Reset Student Attempts
===================================================

When you create a problem, you can limit the number of times that a student can try to answer that problem correctly. If unexpected issues occur for a problem, you can reset the value for one particular student's attempts back to zero so that the student can begin work over again. If the unexpected behavior affects all of the students in your course, you can reset the number of attempts for all students to zero. 

For information about modifying a released problem, including other workarounds, see :ref:`Modifying a Released Problem`.

**Note**: To reset the number of attempts for a problem, you need its unique identifier. See :ref:`find_URL`.

To reset student attempts for a problem:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Student Admin**. 

#. To reset the number of attempts for one student, you work in the Student-Specific Grade Adjustment section of the page. Enter the student's email address or username and the unique problem identifier, then click **Reset Student Attempts**.

#. To reset the number of attempts for all enrolled students, you work in the Course-Specific Grade Adjustment section of the page. Enter the unique problem identifier then click **Reset ALL students' attempts**. 

#. A dialog opens to indicate that the reset process is in progress. Click **OK**. 

   This process does not take long for a single student, but can take some time to complete for all enrolled students. The process runs in the background, so you can navigate away from this page and do other work while it runs.

7. To view the results of the reset process, click either **Show Background Task History for Student** or **Show Background Task History for Problem**.

   A table displays the status of the reset process for each student or problem.

.. _Review_Answers:

****************************************
Student Answer Distribution
****************************************

For certain problems in your course, you can download a CSV file with data about the distribution of student answers. Student answer distribution data is included in the file for problems of these types: 

* Checkboxes (``<choiceresponse>``)
* Dropdown (``<optionresponse>``)
* Multiple choice (``<multiplechoiceresponse>``)
* Numerical input (``<numericalresponse>``)
* Text input (``<stringresponse>``)
* Math expression input (``<formularesponse>``)

The file includes a row for each problem-answer combination selected by your students. For example, for a problem that has a total of five possible answers the file includes up to five rows, one for each answer selected by at least one student. For problems that use rerandomization (the **Randomization** setting in Studio), there is one row for each problem-variant-answer combination selected by your students.

The CSV file contains the following columns:

.. list-table::
   :widths: 20 65
   :header-rows: 1

   * - Column
     - Description
   * - ModuleID
     - The internal identifier for the Problem component.
   * - PartID
     - For a Problem component that contains multiple problems, the internal identifier for each individual problem. For a Problem component that contains a single problem, the internal identifier of that problem. 
   * - Correct Answer
     - 0 if this **AnswerValue** is incorrect, or 1 if this **AnswerValue** is correct.
   * - Count
     - The number of times that students entered or selected this answer as their most recent submission for the problem or problem variant. For problems with the number of **Attempts** set to a value greater than 1, this means that each student contributes a maximum of 1 to this count, even if the same answer is provided in multiple attempts.
   * - ValueID
     - The internal identifier of the answer choice for checkboxes and multiple choice problems. Blank for dropdown, numerical input, text input, and math expression input problems.
   * - AnswerValue
     - The text label of the answer choice for checkboxes, dropdown, and multiple choice problems. The value entered by the student for numerical input, text input, and math expression input problems. 
   * - Variant
     - For problems that use the **Randomization** setting in Studio, contains the unique identifier for a variant of the problem. Blank for problems that do not use the **Randomization** setting, or that use the **Never** option for this setting.
   * - Problem Display Name
     - The **Display Name** defined for the problem.
   * - Question
     - The label for accessibility that appears above the answer choices or the text entry field for the problem. In Studio's Simple Editor, this text is surrounded by two pairs of angle brackets (>>Question<<). Blank for questions that do not have an accessibility label defined.

Entries are sorted by the value in each column, starting with the ModuleID on the left and continuing through the columns to the right.

Please note the following about the student answer distribution report:   

* This report includes only problems that at least one student has answered since early March 2014. For those problems, this report only includes activity that occurred after October 2013. 

* For checkboxes and multiple choice problems, the answer choices actually selected by a student after early March 2014 display as described above. Answer choices selected by at least one student after October 2013, but not selected since early March 2014, are included on the report but do not include an **AnswerValue**. The **ValueID** does display the internal identifiers, such as choice_1 and choice_2, for those answers. 

* For problems that use the **Randomization** setting in Studio, if a particular answer has not been selected since early March 2014, the **Question** is blank for that answer.

* Problem **Count** values reflect the entire problem history. If you change a problem after it is released, it may not be possible for you to determine which answers were given before and after you made the change.

* Some spreadsheet applications can alter the data in the CSV report for display purposes. For example, for different student answers of "0.5" and ".5" Excel correctly includes the two different lines from the CSV, but displays the **AnswerValue** on both of them as "0.5". If you notice answers that appear to be the same on separate lines with separate counts, you can review the actual, unaltered data by opening the CSV file in a text editor.

* The CSV file is UTF-8 encoded, but not all spreadsheet applications interpret and render UTF-8 encoded characters correctly. For example, a student answer distribution report with answer values in French displays differently in Microsoft Excel for Mac than in OpenOffice Calc. 

  Answer Values in Microsoft Excel for Mac:

   .. image:: ../Images/student_answer_excel.png
     :alt: A spreadsheet that replaces accented French characters with underscores

  Answer Values in OpenOffice Calc:

   .. image:: ../Images/student_answer_calc.png
     :alt: A spreadsheet that displays accented French characters correctly

  If you notice characters that do not display as expected in a spreadsheet, try a different spreadsheet application such as LibreOffice or Apache OpenOffice to open the CSV file. (These applications are open-source office suites that are available for download online.)

.. _Download_Answer_Distributions:

===================================================
Download the Student Answer Distribution Report
===================================================

An automated process runs periodically on the edX servers to update the CSV file of student answer data. A link to the most recently updated version of the CSV file is available on the Instructor Dashboard. 

To download the most recent file of student answer data:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Data Download**.

#. At the bottom of the page, click the ``{course_id}_answer_distribution.csv`` file name.

===================================================
View a Histogram of Scores for a Single Problem
===================================================

You can view a chart of the score distribution for a specified problem.

.. note:: In order to view the score distribution for a problem, you need its unique identifier. See :ref:`find_URL`.

To display the distribution of scores for a problem:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Analytics**. 

#. In the Score Distribution section, select a problem by using its unique identifier. 

   A histogram of scores for that problem displays.

   .. image:: ../Images/score_histogram.png
     :alt: Graph of the numbers of students who got different scores for a selected problem

..  **Question**: (sent to Olga 31 Jan 14) this is a tough UI to use: how do they correlate the codes in this drop-down with actual constructed problems? the copy-and-paste UI on the Student Admin page actually works a little better imo.
