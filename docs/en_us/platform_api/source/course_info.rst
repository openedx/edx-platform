##################################################
Course Information API Module
##################################################

.. module:: mobile_api

This page contains docstrings and example responses for:

* `Get Course Updates`_
* `Get Course Handouts`_
* `Get the Course About Page`_
  

.. _Get Course Updates:

*******************
Get Course Updates
*******************

.. .. autoclass:: course_info.views.CourseUpdatesList

**Use Case**

Get the content for course updates.

**Example request**:

``GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/updates``

**Response Values**

A array of course updates. Each course update contains:

* date: The date of the course update.

* content: The content, as a string, of the course update. HTML tags are not
  included in the string.

* status: Whether the update is visible or not.

* id: The unique identifier of the update.

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

.. .. autoclass:: course_info.views.CourseHandoutsList

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


.. _Get the Course About Page:

**************************
Get the Course About Page
**************************

.. .. autoclass:: course_info.views.CourseAboutDetail
..    :members:

**Use Case**

Get the HTML for the course about page.

**Example request**:

``GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/about``

**Response Values**

* overview: The HTML for the course About page.

**Example response**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS

    {
        "overview": "<section class=\"about\">\n
                     <h2>About This Course</h2>\n   
                     <p>Include your long course description here. The long course description should contain 150-400 words.</p>
                     <p>This is paragraph 2 of the long course description. Add more paragraphs as needed. Make sure to enclose them in paragraph tags.</p>
                     </section>\n\n 
                     <section class=\"prerequisites\">\n   
                     <h2>Prerequisites</h2>\n   
                     <p>Add information about course prerequisites here.</p>\n </section>\n\n 
                     <section class=\"course-staff\">\n   
                     <h2>Course Staff</h2>\n   
                     <article class=\"teacher\">\n     
                     <div class=\"teacher-image\">\n       
                     <img src=\"/static/images/pl-faculty.png\" align=\"left\" style=\"margin:0 20 px 0\">\n     
                     </div>\n\n     
                     <h3>Staff Member #1</h3>\n     
                     <p>Biography of instructor/staff member #1</p>\n   
                     </article>\n\n   
                     <article class=\"teacher\">\n     
                     <div class=\"teacher-image\">\n       
                     <img src=\"/static/images/pl-faculty.png\" align=\"left\" style=\"margin:0 20 px 0\">\n     
                     </div>\n\n     
                     <h3>Staff Member #2</h3>\n     
                     <p>Biography of instructor/staff member #2</p>\n   
                     </article>\n 
                     </section>\n\n 
                     <section class=\"faq\">\n   
                     <section class=\"responses\">\n     
                     <h2>Frequently Asked Questions</h2>\n     
                     <article class=\"response\">\n       
                     <h3>Do I need to buy a textbook?</h3>\n       
                     <p>No, a free online version of Chemistry: Principles, Patterns, and Applications, First Edition by Bruce Averill and Patricia Eldredge will be available, though you can purchase a printed version (published by FlatWorld Knowledge) if you\u2019d like.</p>\n     
                     </article>\n\n     
                     <article class=\"response\">\n       
                     <h3>Question #2</h3>\n       
                     <p>Your answer would be displayed here.</p>\n     
                     </article>\n   
                     </section>\n 
                     </section>"
    }
