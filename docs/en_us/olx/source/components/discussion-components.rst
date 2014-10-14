#################################
Discussion Components
#################################

You can add inline discussion components to a vertical, or unit, in your
course.

See:

* `Create the XML File for a Discussion Component`_
* `Discussion Component XML File Elements`_
* `discussion Element Attributes`_
* `Example Discussion Component XML File`_

**********************************************
Create the XML File for a Discussion Component
**********************************************

You create an XML file in the ``discussion`` directory for each inline
discussion component in your course.

The name of the XML file must match the value of the @url_name attribute of the
``discussion`` element in the vertical XML file.

For example, if the vertical XML file contains:

.. code-block:: xml
  
   <vertical display_name="Lesson_1_Unit_1">
      <discussion url_name="Introduce_Yourself"/>
      . . .
  </vertical>

You create the file ``discussion/Introduce_Yourself.xml`` to define the inline
discussion component.

***************************************
Discussion Component XML File Elements
***************************************

The root element of the XML file for the HTML component is file is
``discussion``.

The ``discussion`` element contains not children.

*************************************
``discussion`` Element Attributes
*************************************

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the discussion
       component.
   * - ``discussion_category``
     - The name of the category for the inline discussion as shown in the main
       **Discussion** tab of the course.
   * - ``for``
     - A string that describes the discussion for students.
   * - ``id``
     - The unique identifier that the discussion forum service uses to refer to
       this inline discussion component. This value must be unique across all
       courses in the edX deployment. Therefore it is recommended that you use
       the standard *<course_name>_<course_run>_<descriptor>* as in the above
       example. Do not use a period (.) in the ID value.
   * - ``discussion_id``
     - ???
   * - ``discussion_target``
     - ???


*************************************
Example Discussion Component XML File
*************************************

The following example shows an XML file for a discussion component:

.. code-block:: xml
  
  <discussion 
      discussion_category="Essays" 
      discussion_id="6e51dd8f181b44ffa6d91303a287ed3f" 
      discussion_target="Peer Grading" 
      display_name="Peer Grading"
   /> 
