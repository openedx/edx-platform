.. _HTML Components:

#################################
HTML Components
#################################

See:

* `Create the HTML Component`_
* `Example of an HTML Component Embedded in a Vertical`_
* `Example of Separate HTML Files`_
* `HTML Component XML File Elements`_
* `html Element Attributes`_
* `Example HTML Component XML File`_
* `Example HTML Component Content`_


*********************************************
Create the HTML Component
*********************************************

To add an HTML component to your course, you can embed the XML for it in the
parent XML file, or split it up into either 1 or 2 additional files. You can
break up the HTML configuration into an .xml file in the html directory and an
additional .html file in the same directory. 

.. caution:: If you are including HTML that is not valid HTML, you must break out HTML content in a separate file.


*****************************************************
Example of an HTML Component Embedded in a Vertical
*****************************************************

.. code-block:: xml
  
   <vertical display_name="Lesson_1_Unit_1">
      ...
      <html>The above has an error. <b>x</b> should be <b>y</b> in the second equation.</html>
  </vertical>


*********************************************
Example of Separate HTML Files
*********************************************

You create an XML file in the ``html`` directory for each HTML component in
your course.

The name of the XML file must match the value of the @url_name attribute of the
``html`` element in the vertical XML file.

For example, if the vertical XML file contains:

.. code-block:: xml
  
   <vertical display_name="Lesson_1_Unit_1">
      <html url_name="Introduction"/>
      . . .
  </vertical>

You create the file ``html/Introduction.xml`` to define the HTML component.

*************************************
HTML Component XML File Elements
************************************* 

The root element of the XML file for the HTML component is file is ``html``. 

In this case, the ``html`` element contains no children.

*************************************
``html`` Element Attributes
*************************************

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the HTML
       component.
   * - ``file_name``
     - The name of the HTML file that contains the content for the HTML
       component, without the ``.HTML`` extension.

*************************************
Example HTML Component XML File
*************************************

The following example shows an XML file for an HTML component:

.. code-block:: xml
  
  <html filename="Introduction" display_name="Unit Introduction"/>  


*************************************
Example HTML Component Content
*************************************

In the component's HTML file, you add valid HTML to represent the content you
want to be displayed to students. For example, the following is from an HTML
file for the edX Demo course:

.. code-block:: html
  
    <h2>Lesson 2: Let's Get INTERACTIVE!</h2> 
    <p>
    <img
    src="/static/interactive_x250.png" alt="Interactive" width="250"
    hspace="12" vspace="12" border="0" align="right" />Now that you know your
    way around an edX course let's look at some of the exciting interactive
    tools you may encounter. Use the learning sequence above to explore.
    &nbsp;</p> 
    <p>Once you have tried the interactive tools in this lesson,
    make sure to check out the week 2 homework where we show you several of the
    really cool interactive labs we&rsquo;ve created for past courses.
    &nbsp;They&rsquo;re fun to play with. &nbsp;Many courses will have tools
    and labs that you need to use to complete homework assignments.</p>

