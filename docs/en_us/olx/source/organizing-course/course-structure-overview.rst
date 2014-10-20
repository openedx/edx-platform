.. _OLX Course Building Blocks:

###############################
OLX Course Building Blocks
###############################

Before you begin building OLX, you should understand the building blocks of an
edX course. See:

* `Courseware`_
* `Supplemental Course Content`_
* `Course Policies`_

**************
Courseware
**************

Courseware is the main content of your course and consists mainly of lessons
and assessments. The following list describes how courseware is organized in
OLX:

* Course chapters are at the top level of your course and typically
  represent a time period. In Studio, chapters are called *sections*.

* A chapter contains one or more children which correspond to
  top-level pages in the course. In Studio, these are called 'subsections' and
  are currently restricted to ``sequential`` elements at this
  level. OLX supports any XBlock at this level. 

* Courses are composed of structural elements, such as ``sequential``
  and ``vertical``, and leaf-nodes or content elements, such as
  ``html`` or ``problem``. Studio has a fixed hierarchy where children
  of ``sequential`` elements are ``vertical`` elements (called units),
  and children of ``vertical`` elements are leaf elements (called modules). 

  * :ref:`Course Components`
  * :ref:`Problems`
    
For more information, see :ref:`The Courseware Structure`.

****************************
Supplemental Course Content
****************************

In addition to the courseware described above, you course can contain
supplemental content, such as textbooks, custom pages, and files.  The
following list describes the types of supported content:

* Course about pages appear in the course list for prospective students and are
  used to market your course. For more information, see :ref:`The Course About
  Pages`.

* Course assets are any supplemental files you use in your course, such as a
  syllabus as a PDF file or an image that appears in an HTML component. For
  more information, see :ref:`Course Assets`.

* Course pages are custom pages that you can have appear in the top navigation
  menu of your course.  For more information, see :ref:`Course Tabs`.

****************************
Course Policies
****************************

Course policies determine how your course functions. For example, policies
control grading and content experiments. For more information, see
:ref:`Policies`.
