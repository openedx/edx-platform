.. _Course Policies:

#################################
Course Policies
#################################

You create a course policy file to specify metadata about your course.

*******************************
Create the Course Policy File
*******************************

You define policies for your course in the ``policy.json`` file. 

Save the ``policy.json`` file in the ``policy/<course-name>`` directory. 

The ``<course-name>`` directory  must match the value of the ``url_name`` attribute in the ``course.xml`` file.


************************************
Course Policy JSON Objects
************************************

  .. list-table::
     :widths: 10 80
     :header-rows: 0

     * - ``start``
       - The start date for the course.  For example: ``"2012-09-05T12:00"``.
     * - ``advertised_start``
       - The start date displayed in the course listing and course about pages.
         For example: ``"2012-09-05T12:00``.
     * - ``disable_policy_graph``
       - Whether the policy graph should be disabled (``true``) or not (``false)``.  SUPORTED?
     * - ``enrollment_start``, ``enrollment_end``
       - The dates in which students can enroll in the course. For example, ``"2012-09-05T12:00"``. If not specified, students can enroll any time. 
     * - ``end``
       - The end date for the course.  For example: ``"2012-11-05T12:00"``.
     * - ``end_of_course_survey_url``
       - The url for an end of course survey. The link is shown after the course is over, next to certificate download links.
     * - ``tabs``
       - Custom pages, or tabs, in the courseware.  See below for details.
     * - ``discussion_blackouts``
       - An array of time intervals during which students cannot create or edit discussion posts. Moderators, Community TAs, and Administrators are not restricted by these dates. For example, you could specify blackout dates during exams. For example: ``[[""2012-10-29T04:00", "2012-11-03T04:00"], ["2012-12-30T04:00", "2013-01-02T04:00"]]``. Moderators, Community TAs, and Administrators are not restricted during blackout periods.
     * - ``show_calculator``
       - Whether the calculator is shown in the course (``true``) or not (``false)``.
     * - ``days_early_for_beta``
       - The number of days early that students in the beta-testers group can
         access the course.
     * - `cohort_config`
       -
          * ``cohorted`` : boolean.  Set to ``true`` if this course uses
            student cohorts.  If so, all inline discussions are automatically
            cohorted, and top-level discussion topics are configurable via the
            cohorted_discussions list. Default is not cohorted).
          * ``cohorted_discussions``: list of discussions that should be
            cohorted.  Any not specified in this list are not cohorted.
          * ``auto_cohort``: ???
          * ``auto_cohort_groups``: ``["group name 1", "group name 2", ...]``
            `If ``cohorted`` and ``auto_cohort`` are ``true``, automatically
            put each student into a random group from the
            ``auto_cohort_groups`` list, creating the group if needed.
     * - ``pdf_textbooks``
       - have pdf-based textbooks on tabs in the courseware.  See below for
         details.
     * - ``html_textbooks``
       - have html-based textbooks on tabs in the courseware.  See below for
         details.

*******************************
Example Course Policy File
*******************************

.. code-block:: json

    {
      "course/2014":
          {
	          "tabs": [{"type": "courseware", "name": "Courseware"}, 
	                   {"type": "course_info", "name": "Course Info"}, 
	                   {"type": "discussion", "name": "Discussion"}, 
	                   {"type": "wiki", "name": "Wiki"}, 
	                   {"type": "progress", "name": "Progress"}],
	
	           "display_name": "edX Demonstration Course",
	           "discussion_topics": {"General": {"id": "i4x-General-course-2014"}}
               
                   "user_partitions": [{"id": 0,
                                        "name": "Two Groups",
                                        "description": "For 2-group experiments.",
                                         "version": 1,
                                         "groups": [{"id": 0,
                                                     "name": "Group A",
                                                     "version": 1},
                                                    {"id": 2,
                                                     "name": "Group B",
                                                     "version": 1}]
                                       }]
          }
    }