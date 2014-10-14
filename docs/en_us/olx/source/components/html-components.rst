.. _HTML Components:

#################################
HTML Components
#################################

To add an HTML component to your course, you create both XML and HTML files.

See:

* `Create the XML File for an HTML Component`_
* `HTML Component XML File Elements`_
* `html Element Attributes`_
* `Example HTML Component XML File`_
* `Create the HTML File for an HTML Component`_
* `Example HTML Component Content`_

  
Both files, for each component, must be in the ``html`` directory.

*********************************************
Create the XML File for an HTML Component
*********************************************

You create an XML file in the ``html`` directory for each HTML component in your course.

The name of the XML file must match the value of the @url_name attribute of the ``html`` element in the vertical XML file.

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

The ``html`` element contains not children.

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


*********************************************
Create the HTML File for an HTML Component
*********************************************

You create an HTML file in the ``html`` directory for each HTML component in your course.

The name of the HTML file must match the value of the @file_name attribute of the ``html`` element in the component's XML file.

For example, if the component's XML file contains:

.. code-block:: xml
  
  <html filename="Introduction" display_name="Unit Introduction"/> 

You create the file ``html/Introduction.html`` to define the HTML component content.

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



