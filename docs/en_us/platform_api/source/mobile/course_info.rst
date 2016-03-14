##################################################
Mobile API Course Information Resource
##################################################

With the Mobile API **Course Information** resource, you can complete the
following tasks.

.. contents::
   :local:
   :depth: 1
  
.. _Get Course Updates:

*******************
Get Course Updates
*******************

.. autoclass:: mobile_api.course_info.views.CourseUpdatesList

**Example response**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS

    [
        {
            "date": "October 4, 2014", 
            "content": "Reminder about the quiz due today. 
            "status": "visible", 
            "id": 2
        }, 
 
        { "date": "October 1, 2014", 
          "content": "Welcome to the course. We
            built this to help you become more familiar with taking a course on
            edX prior to your first day of class. \n<br>\n<br>\nIn a live course,
            this section is where all of the latest course announcements and
            updates would be., 
            "id": 1 } ]

.. _Get Course Handouts:

*******************
Get Course Handouts
*******************

.. autoclass:: mobile_api.course_info.views.CourseHandoutsList

**Example response**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS

    {
        "handouts_html": "\n\n<ol class=\"treeview-handoutsnav\">\n
                          <li><a href=\"/static/demoPDF.pdf\">Example handout</a></li> 
                          </ol>\n\n"
    }

