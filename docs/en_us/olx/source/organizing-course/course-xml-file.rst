.. _The Courseware Structure:

##########################
The Courseware Structure
##########################

You develop the courseware structure in the ``course.xml`` file, in the top-
level directory.

See:

* `The course.xml File`_
* `Course Chapters`_
* `Course Sequentials`_
* `Course Verticals`_

*************************************
The ``course.xml`` File
*************************************

The root element of the ``course.xml`` file is ``course``. 

The ``course`` element does not contain any child elements.

For example, the ``course.xml`` file may contain:

.. code-block:: xml
  
  <course advanced_modules="[&quot;concept&quot;, &quot;done&quot;,
      &quot;profile&quot;, &quot;recommender&quot;]" course="edX_Insider"
      course_image="code.png" display_name="edX Demo"
      enrollment_start="2014-03-01T04:00:00Z" org="edX"
      start="2014-03-03T00:00:00Z" url_name="Ongoing">
      . . .
      . . .

==============================
``course`` Attributes
==============================

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``advanced_modules``
     - The list of advanced modules, or custom XBlocks, used in your course.
   * - ``url_name``
     - The value in the course URL path directly after the domain,
       organization, and course name. The url_name must also be the name of the course outline XML file (without the ``.xml`` extension).
   * - ``org``
     - The organization sponsoring the course. This value is in the course URL
       path, following the domain and ``/courses/``.
   * - ``course``
     - The name of the course. This value is in the course URL
       path, following the organization.
   * - ``course_image``
     - The filename of the image used on the course About page.
   * - ``enrollment_start``
     - The date and time that students can start enrolling in the course.


============================================================
``course`` Element Attributes and Course URLS
============================================================

The attributes of the ``course`` element are used to construct URLs in the
course.  The following course URL shows where these values are used:

.. code-block:: html
  
  http://my-edx-server.org/courses/<@org value>/<@course value>/<@url_name value>/info

For example:

.. code-block:: html
  
  http://my-edx-server.org/courses/edX/DemoX/Demo_Course/info

*******************************
Course Chapters
*******************************

You create a course chapter with the ``chapter`` element, as a child of the root ``course`` element. 

For example, if the course outline file contains:

.. code-block:: xml
  
    <course> 
      <chapter display_name="Exam Review" url_name="exam_review"> 
      . . .
    </course>

==============================================
``chapter`` Attributes
==============================================

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the chapter, or
       section.
   * - ``start``
     - The date and time, in UTC, that the chapter is released to students.
       Before this date and time, students do not see the chapter.

=========================
``chapter`` Children
=========================

The ``chapter`` element contains one or more child ``sequential`` elements. 

The ``sequential`` element references a sequential, or subsection, in the
course.

The following example shows a chapter with two sequentials, or subsections. :

.. code-block:: xml
  
  <chapter display_name="Example Week 2: Get Interactive">
      <sequential display_name="Simulations" url_name="simulations"> 
          . . .
      <sequential display_name="Graded Simulations" 
          url_name="graded_simulations"> 
          . . .
  </chapter>


*******************************
Course Sequentials
*******************************

You create a course sequential with the ``sequential`` element, for each
subsection in the chapter.

For example, the course may contain:

.. code-block:: xml
  
    <course> 
        <chapter url_name="exam_review"> 
            <sequential display_name="Simulations" url_name="simulations">
                . . .
            </sequential>
        </chapter>
        . . .
    </course>

==============================================
``sequential`` Attributes
==============================================

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the sequential,
       or subsection.
   * - ``start``
     - The date and time, in UTC, that the sequential is released to students.
       Before this date and time, students do not see the sequential.
   * - ``graded``
     - Whether the sequential is a graded subsection; ``true`` or ``false``.
   * - ``format``
     - If the sequential is graded, the assignment type.
   * - ``graceperiod``
     - If the sequential is graded, the number of seconds in the grace period.
   * - ``rerandomize``
     - TBP
   * - ``showanswer``
     - TBP
   * - ``xqa_key``
     - TBP

==============================================
``sequential`` Children
============================================== 

The ``sequential`` element contains one or more child ``vertical`` elements. 

The ``veritical`` element references a vertical, or unit, in the course.

The following example shows a chapter with a sequential that has three verticals, or units. :

.. code-block:: xml
  
    <course> 
        <chapter url_name="exam_review"> 
            <sequential display_name="Simulations" url_name="simulations">
                <vertical display_name: "Unit 1" url_name="Lesson_1_Unit_1">
                    . . . .
                <vertical display_name: "Unit 2" url_name="Lesson_1_Unit_2">
                    . . . .
            </sequential>
        </chapter>
        . . .
    </course>


*******************************
Course Verticals
*******************************

A course vertical:

* Defines the display name for the vertical, or unit.
* Organizes components and other verticals in the vertical.

You create a course vertical with the ``vertical`` element, for each
unit in the subsection.

For example, the course may contain:

.. code-block:: xml
  
    <course> 
        <chapter url_name="exam_review"> 
            <sequential display_name="Simulations" url_name="simulations">
                <vertical display_name="Unit 1" url_name="Lesson_1_Unit_1"/>
                    . . .
            </sequential>
        </chapter>
        . . .
    </course>

=========================
``vertical`` Attributes
=========================

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the sequential,
       or subsection.


==============================
``vertical`` Children
============================== 

The ``vertical`` element contains one or more child elements for each component
in the vertical, or unit.

note:: 
  You can embed the content of components in the ``course.xml`` file, as
  child elements of the ``vertical`` element. Hoever, you may want to store
  components in separate files, to better enable content reuse across courses.

A vertical element can also contain a vertical element. You can nest
verticals, or units, recursively.

Child elements of ``vertical`` refer to components in your course.  The edX
Platform supports a wide range of components, including custom XBlocks.

The following example shows a vertical with two components:

.. code-block:: xml
  
  <vertical display_name="Lesson_1_Unit_1">
      <html url_name="Introduction"/>
      <video url_name="Unit_1_Video"/>
  </vertical>
