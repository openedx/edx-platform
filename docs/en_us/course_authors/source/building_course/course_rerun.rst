.. _Rerun a Course:

###################
Re-run a Course
###################

Another way to create a course in Studio is to re-run an existing course. When
you select the course re-run option, most, but not all, of the original course
content is duplicated to the new course. The original course is not changed in
any way.

.. list-table::
   :widths: 45 45
   :header-rows: 1

   * - Type of Content
     - Duplicated to New Course?
   * - Course start date
     - No. Set to January 1, 2030.
   * - All other course dates
     - Yes.  
   * - Course outline structure (sections, subsections, units)
     - Yes. 
   * - Individual problems and other components
     - Yes.
   * - Files uploaded to the course, including videos and textbooks
     - Yes.
   * - Pages added to the course
     - Yes, including all page content and the defined page order.
   * - Course Updates 
     - Yes.
   * - Advanced Settings
     - Yes.
   * - Grading policy
     - Yes.
   * - Student enrollment data
     - No.
   * - Course team privileges, including admins, discussion moderators, and beta testers
     - No. Only your own role (as a course admin and instructor) is defined.
   * - Discussion posts, responses, comments, and other data
     - No.
   * - Student answers, progress, and grading data
     - No.
   * - Certificates
     - No.

.. for the course outline structure row above, indicate that the state remains/does not remain the same (published vs. hidden)

See :ref:`Create a Course Using Rerun` and :ref:`Update the New Course`.

.. _Create a Course Using Rerun:

********************************************
Use Re-Run to Create a Course
********************************************

Before you re-run a course, verify that:

* You have permission to create courses in Studio. See :ref:`Use Studio on Edge`.

.. is it appropriate that we don't have an analogous description for getting course creator privs on edx.org?

* You are a member of the course staff for the course that you want to re-run.

* The original course was created in Studio, not in XML.

To re-run a course:

#. Log in to Studio. Your dashboard lists the courses that you have access to
   as a staff memeber.

#. Move your cursor over each row in the list of courses. The **Re-Run Course**
   and **View Live** options appear for each course.

#. Locate the course you want to re-run and click **Re-Run Course**.

  .. image:: ../Images/rerun_course_info.png
     :alt: The course creation page for a rerun, with the course name, organization, and course number supplied

.. this image ^ is from the wireframe and needs to be replaced     

4. Supply a **Course Run** timeframe for the new course. The course number, the
   organization, and the course run are used to create the URL for the new
   course. The combination of these three values must be unique for the new
   course.

.. any of the 4 values can be changed, but we are not currently supporting
.. cross-organization use such as licensing

5. Click **Create Re-Run**. The duplication process takes several minutes. You
   can work in other parts of Studio or in the LMS, or on other web sites,
   while the process runs.

  The new course appears on your **My Courses** dashboard in Studio when
  configuration is complete.

.. _Update the New Course:

********************************************
Update the New Course
********************************************

When you create a course by re-running another course, you should carefully
review the course settings and content. At a minimum, you will need to make
these changes to prepare the new course for release:

* Add course staff members. See :ref:`Add Course Team Members` or
  :ref:`Course_Staffing`.
  
* Update course-wide dates, including course and enrollment start and end
  dates. See :ref:`Set Important Dates for Your Course`.

* Change the release dates of course sections, subsections, and units. See
  :ref:`Release Dates`.

* Change the due dates of subsections that are part of your grading policy. See
  :ref:`subsections`.

* Delete or edit posts on the **Course Updates** page in Studio. See :ref:`Add
  a Course Update`.

* Review the staff biographies and other information on the course summary
  page and make needed updates. See :ref:`The Course Summary Page`.

* Add initial wiki articles.

* Create initial posts for discussion topics and an "introduce yourself"
  post. See :ref:`Discussions`.
  
You can use the :ref:`course checklists<Use the Course Checklist>` to work
through the course and verify that it is ready for release.

To assure a quality experience for course students, be sure to test a course
created with the re-run option thoroughly before the course start date.
See :ref:`Testing Your Course` and :ref:`Beta_Testing`.