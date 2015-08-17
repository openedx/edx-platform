##################################################
Mobile Course Information API
##################################################

This page describes how to use the Mobile Course Information API
to complete these actions:

* `Get Course Updates`_
* `Get Course Handouts`_
  

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

**Use Case**

Get the HTML for course handouts.

**Example request**:

``GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/handouts``

**Response Values**

* handouts_html: The HTML for course handouts.

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

