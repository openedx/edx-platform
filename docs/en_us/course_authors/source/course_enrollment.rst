.. _Enrollment:

##########################
Enrollment
##########################

Course authors and instructors can enroll students in a course, see how many people are enrolled, and, when necessary, unenroll students.

Students can enroll themselves in a course during its defined enrollment period. For a ``www.edx.org`` course, enrollment is publicly available to anyone who registers an edX account. For other courses, such as those on ``edge.edx.org``, enrollment is limited to the students that you explicitly enroll and the students to whom you give the course URL. 

* :ref:`registration_enrollment`

* :ref:`enroll_student`

* :ref:`view_enrollment_count`

* :ref:`unenroll_student`

.. _registration_enrollment:

*********************************
Registration and Enrollment
*********************************

Before a student can be enrolled in a course, he or she must:

#. Register a user account, which includes supplying a valid email address, on ``www.edx.org``, ``edge.edx.org``, or your implementation of the edX platform.

#. Activate the registered account by following the emailed instructions.

Students can then enroll themselves in edx.org courses, or can enroll in other courses if they know the URL. For a more detailed description of this process from a student's point of view, see :doc:`appendices/c`. 

Course authors and instructors can enroll students in a course either before or after the students register their user accounts. 

To work on a course, all course staff members must also be registered and enrolled.

.. _enroll_student:

*********************************
Enroll Students in a Course
*********************************

You enroll students, and other course staff members, in your course by supplying their email addresses. After the **Enrollment End Date** for a course students can no longer enroll themselves; however, you can still explicitly enroll students.

When you enroll students, you have options to:

* **Auto Enroll**. Enrolls any student who already has a registered user account in the course immediately. Students who are not registered are enrolled as soon as they register and activate a user account for the same email address. As a result, students do not need to complete the explicit course enrollment step.

* **Notify students by email**. The email message includes the name of the course, a link to the registration page, and a reminder to use the same email address to register that you supplied for the student. Whether you choose to send a notification or not, enrolled students see your course on their dashboard when they log in.

  An example of the email message that students receive when you select this option follows.

  .. image:: Images/Course_Enrollment_Email.png
        :alt: Email message inviting a student to enroll in the EdX 101 course

To enroll students or staff members:

#. View the live version of your course.

#. Click **Instructor** then **Try New Beta Dashboard**.

#. Click **Membership**. 

#. In the Batch Enrollment section of the page, enter an email address or multiple addresses separated by commas or line feeds.

  You can copy and paste data from a CSV file of email addresses. However, note that this feature is better suited to courses with smaller enrollments, rather than courses with massive enrollments. 

5. Optionally, select **Auto Enroll** to streamline the course enrollment process for the students. 

#. Optionally, select **Notify students by email** to send students email. 

#. Click **Enroll**.

.. _view_enrollment_count:

***************************
View an Enrollment Count
***************************

After you create a course, you can access the total number of people who are enrolled in it. When you view an enrollment count, note that:

* In addition to students, the enrollment count includes the course author, course team members, instructors, and course staff. (In order to work with a course in Studio or the LMS, you must be enrolled in it.)

* Students can unenroll from courses, and course authors and instructors can unenroll students when necessary. 

  **Note**: The enrollment count displays the number of currently enrolled students and course team staff. It is not a historical count of everyone who has ever enrolled in the course.

To view the enrollment count for a course:

#. View the live version of your course.

#. Click **Instructor** then **Try New Beta Dashboard**.

#. Click **Course Info** if necessary. 

  The Enrollment Information section of the page that opens shows the total number of people who are currently enrolled. 

You can also view or download a list of the people who are enrolled in the course. See :ref:`Student Data`.

.. _unenroll_student:

*********************************
Unenroll students from a course
*********************************

You can remove students from a course by unenrolling them. To prevent students from re-enrolling, course enrollment must also be closed. You use Studio to set the **Enrollment End Date** for the course to a date in the past. See :ref:`Set Important Dates for Your Course`.

To unenroll students, you supply the email addresses of enrolled students. 

**Note**: Unenrollment does not delete data for a student. An unenrolled student's state remains in the database and is reinstated if the student does re-enroll. 

#. View the live version of your course.

#. Click **Membership**. 

#. In the Batch Enrollment section of the page, enter an email address or multiple addresses separated by commas or line feeds.

#. Click **Unenroll**. The course is no longer listed on the students' dashboards, and the students can no longer contribute to discussions or the wiki or access the courseware.

