###############################
OLX Course Building Blocks
###############################

Before you begin building OLX, you should understand the
building blocks of an edX course. See:

* `Courseware`_
* `Supplemental Course Content`_
* `Course Policies`_

**************
Courseware
**************

Courseware is the main content of your course, namely lessons and assessments.
The following list describes how courseware is organized in OLX:

* Course sections are at the top level of your course and typically represent a
  time period. In OLX, sections are represented by ``chapter`` elements. 

* A section contains one or more subsections. Course subsections are parts of a
  section, and usually represent a topic or other organizing principle. In
  OLX, subsections are represented by ``sequential`` elements. 

* A subsection contains one or more units. In OLX, units are represented by
  ``vertical`` elements.  

* Course units are lessons in a subsection that students view as single pages.
  A unit contains one or more components. Course components are objects within
  units that contain your actual course content. For more information, see:

  * :ref:`Course Components`
  * :ref:`Problems and Tools`
  * :ref:`Advanced Components`
    
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
  menu of your course.  For more information, see :ref:`Course Pages`.

****************************
Course Policies
****************************

Course policies determine how your course functions. For example, policies
control grading and content experiments. For more information, see
:ref:`Policies`.