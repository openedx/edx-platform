.. _Launch:

##############################
Course Launching Activities 
##############################

To launch a course, you prepare the course itself, the staff, and the
students. This chapter includes a :ref:`Course Launch Checklist` to use as a
model for your schedule of activities.

To help you communicate to the staff and to all course participants when you
are launching the course, and also while the course runs, you can send email
messages from the Instructor Dashboard. See :ref:`Bulk Email` and :ref:`Email
Task History Report`.

.. _Course Launch Checklist:

****************************
Course Launch Checklist
****************************

As the start date for your course approaches, a checklist or timeline of
activities can help you make sure that your course, and your students, are
ready to begin. Suggestions for activities to complete before your course
starts follow.

**Verify Course Settings**

* Check the course start date and time in Studio. See :ref:`Set Important
  Dates for Your Course`.
* Review the grading policy, and set a grace period for homework assignment
  due dates. See :ref:`Establish a Grading Policy`.


**Review First Week Content**

* Verify that all units are present and published. See :ref:`Units`.
* Check all assignments for completeness and verify their due dates. See
  :ref:`Working with Problem Components`.
* Verify that videos, transcripts, and download links are in place and
  working.
* Review feedback from the course team and beta testers to be sure that the
  content has been thoroughly reviewed and tested.

**Welcome Students**

* Two months before the course start date, prepare and send a welcome email
  message to currently enrolled students. See :ref:`Send_Bulk_Email`.
* Compose a welcome message and add it to the **Course Info** page. See :ref:`Add
  a Course Update`.
* Verify that a syllabus and other references are available on the **Course
  Handouts** page. See :ref:`Add Course Handouts`.
* One month before the course start date, prepare and send a welcome email
  message to currently enrolled students.
* One week before the course start date, prepare and send a welcome email
  message to currently enrolled students.
* Start an "Introduce Yourself" topic in a discussion thread. For a MOOC, you
  may want to manage the size of the thread by distributing student responses
  across multiple threads. For example, you can start different threads for
  introductions based on geographical location, such as "Introduce Yourself:
  Europe", "Introduce Yourself: North America", etc. See
  :ref:`Running_discussions`.
* On the course start date, prepare and send a launch email message to
  currently enrolled students.

**Prepare Staff**

* Define communication methods for all course contributors, including staff,
  instructors, and the discussion team. For example, set up a course-specific
  email address.
* Verify that all course contributors know how to record their work, report
  issues, and collaborate on tasks.
* Verify that the instructors and course staff selected for your course
  have the correct role assignments in the LMS. See :ref:`Course_Staffing`.
* Verify that discussion admins, discussion moderators, and community TAs have
  registered and activated their user accounts, enrolled in the course, and been
  assigned their roles. See :ref:`Assigning_discussion_roles`.
* Define methods for managing discussions and guidance for discussion
  moderators, and distribute to the discussion team. See
  :ref:`Moderating_discussions` and :ref:`Guidance for Discussion Moderators`.

.. _Bulk Email:

*************************
Bulk Email 
*************************

With the bulk email feature, you can send email messages to course
participants directly from the Instructor Dashboard. Messages can use HTML
styling, and can include links to videos, social media pages for the course,
and other material. All course contributors who are assigned the course staff
or instructor role can use this feature to communicate with course
participants before, during, and after the course run.

.. note:: The bulk email feature is currently in limited release, and is enabled for new courses only. A gradual rollout of this feature is planned for 2014.

===========================
Message Addressing
===========================

When you send an email message from the Instructor Dashboard, you choose its
recipients by selecting one of these predefined groups:

* **Myself**, to test out a message before sending it to a larger group.
* **Staff and Instructors**, to contact other members of the administrative
  team.
* **All (students, staff and instructors)**, to communicate with currently
  enrolled students and the administrative team. 

  Email messages are not sent to every enrolled student. Students can opt not to
  receive email messages through the **Email Settings** link present on their
  dashboards for each course. Email messages are not sent to these students. In
  addition, email is not sent to students who are enrolled in the course but who
  have not yet activated their user accounts.

When you use the bulk email feature, consider that messages **cannot be
cancelled** after they are sent. Before you send a message to all course
participants, be sure to review each draft carefully, and send the message to
yourself for thorough testing.

.. _Send_Bulk_Email:

======================================================
Send Email Messages to Course Participants
======================================================

To send an email message to course participants:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Email**.

#. Select who you want to send the message to from the **Send to** dropdown
   list. You can select:

  * **Myself**
  * **Staff and Instructors**
  * **All (students, staff and instructors)**

5. Enter a **Subject** for the message. A subject is required.

#. Enter the the text for the message. Messages can use HTML styling,
   including text formatting and links. The email message editor offers the
   same formatting options as the HTML component editor in Studio. See
   :ref:`Working with HTML Components`.

#. Click **Send Email**.  The status of the message displays in the **Pending
   Instructor Tasks** section of the page.

======================================================
Message Queueing
======================================================

When you send a message, it is queued for processing as a bulk email task.
Multiple courses use the same queue to complete these tasks, so it can take
some time for your message to be sent to all of its recipients. If your course
is a MOOC, consider limiting the number of messages that you send to all
course participants to no more than one per week.

On the **Email** page, the **Pending Instructor Tasks** section shows the
status of queued messages.

.. image:: ../Images/Bulk_email_pending.png
       :width: 800
       :alt: Information about an email message, including who submitted it and when, in tabular format

You can perform other tasks on the Instructor Dashboard or navigate to other
pages while you wait for your message to be sent.

.. _Email Task History Report:

********************************
Email Task History Report
********************************

You can produce a report of all of the bulk email tasks sent for your course.
For each message sent, the report includes the username of the requester, the
date and time it was submitted, the duration and state of the entire 
task, the task status, and the task progress.

You can use this history to investigate questions relating to the bulk email
message that have been sent, such as:

* How frequently students are sent course-related email messages.
* Whether a message was sent successfully.
* The number of people who were sent course-related messages over time.

======================================
Review the Email Task History
======================================

To produce the Email Task History report:

#. View the live version of your course.

#. Click **Instructor** > **Try New Beta Dashboard**.

#. Click **Email**. 

#. In the **Email Task History** section of the page, click **Show Email Task
   History**. A report like the following example displays on the Instructor
   Dashboard.

.. image:: ../Images/Bulk_email_history.png
       :width: 800
       :alt: A tabular report with a row for each message sent and columns for requester, date and time submitted, duration, state, task status, and task progress.

For messages with a State of "Success", the Task Progress can show an
informational message such as "Message successfully emailed for 13457 recipients
(skipping 29) (out of 13486)". To interpret this message, note that:

* The first number indicates the number of messages sent to the selected
  recipients.
* The second number ("skipping") indicates the number of enrolled users who will
  not be sent the message. This count includes students have opted out of
  receiving course email messages and students who have not yet activated their
  user accounts.
* The final number ("out of") indicates the number of users in the set of
  recipients you selected who were enrolled in the course when you sent the
  email message. For email messages addressed to a large number of users, the
  number of enrolled students can change while the message is queued for
  processing.
