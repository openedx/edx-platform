.. _Custom JavaScript Applications:

##########################################
Custom JavaScript Applications
##########################################


*******************************
Overview
*******************************


You can include custom JavaScript applications (also called custom JavaScript
problems or JS Input problems) in a course. You add the application directly
into edX Studio.

When you create a JavaScript application, Studio embeds the problem in an inline
frame (HTML ``iframe`` tag) so that students can interact with it in the LMS.

See the following sections for more information:

* `Grading Options for Custom JavaScript Applications`_
* `Use a JavaScript Application Without Grading`_
* `Use a JavaScript Application for a Summative Assessment`_
* `Grade the Student Response with Python`_
* `XML for Custom JavaScript Applications`_

See :ref:`The Custom JavaScript Display and Grading Example Template` for
information about the template application built in to edX Studio.

Course staff should see the following sections of the document `Building and Running an edX Course <http://edx.readthedocs.org/projects/ca/en/latest/>`_:

* `Custom JavaScript Display and Grading <http://edx.readthedocs.org/projects/ca/en/latest/problems_tools/advanced_problems.html#custom-javascript-display-and-grading>`_ 

* `Establishing a Grading Policy <http://edx.readthedocs.org/projects/ca/en/latest/building_course/establish_grading_policy.html>`_ 

The rest of this section provides more information for developers who are
creating JavaScript applications for courses on the edX platform.

.. note:: This section assumes proficiency with JavaScript and with how problems
 are constructed in edX Studio. If you intend to grade students' interactions
 with your JavaScript application, you must also be proficient with Python.



*******************************************************
Grading Options for Custom JavaScript Applications
*******************************************************

When using a JavaScript application in your course content, you have three
options:

#. A JavaScript application that visually demonstrates a concept or process. The
   application would not require student interaction, and students would not be
   graded.

#. A JavaScript application that requires student interaction but does not grade
   performance. Referred to as a formative assessment, such an application
   provides feedback to students based on their interactions.

#. A JavaScript application that requires and grades student interaction.
   Referred to as a summative assessment, such an application can be used to
   evaluate student learning against a standard. To use the JavaScript
   application as a summative assessment and have student performance integrated
   into the edX grading system, you must also use basic Python code in the
   component.

These options are explained through examples below.

*******************************************************
Use a JavaScript Application Without Grading
*******************************************************

The simplest option is to use JavaScript to show content to students, and
optionally to provide feedback as a formative assessment.

#. In edX Studio, upload an HTML file that contains the JavaScript you want to
   show students.
#. Copy the **Embed URL** of the file. 
#. `Create a Custom JavaScript Display and Grading Problem <http://edx.readthedocs.org/projects/ca/en/latest/problems_tools/advanced_problems.html#custom-javascript-display-and-grading>`_. The template
   for the problem contains the definition for a sample JavaScript application
   that requires and grades student interaction.
#. Edit the XML of the component to remove grading information and refer to the
   HTML file you uploaded:

.. code-block:: xml

    <customresponse>
        <jsinput
         width="width needed to display your application"
         height="height needed to display your application"
         html_file="Embed URL of the HTML file"
         sop="false"/>
    </customresponse>

For example:

.. code-block:: xml

    <customresponse>
        <jsinput
         width="400"
         height="400"
         html_file="/static/electrol_demo.html"
         sop="false"/>
    </customresponse>


**************************************************************
Use a JavaScript Application for a Summative Assessment
**************************************************************

To use a JavaScript Application for a summative assessment and have student
results calculated by the edX grading system, you must:

* Include required functions in the JavaScript application.

  * `getState() Function`_
  * `setState() Function`_
  * `getGrade() Function`_

* Reference functions in the problem XML.

* `Grade the Student Response with Python`_.


====================
getState() Function
====================

Your application must contain a ``getState()`` function that returns the state
of all objects as a JSON string.

The ``getState()`` function retrieves the state of objects in the application,
so each student experiences that application in its initial or last saved state.

The name of the ``getState()`` function must be the value of the ``get_statefn``
attribute of the ``jsinput`` element for the problem.

For example:

.. code-block::  xml

    <customresponse cfn="vglcfn">
        <jsinput get_statefn="JSObject.getState"
            . . . .



====================
setState() Function
====================

Your application must contain a ``setState()`` function.

The ``setState()`` function is executed when the student clicks **Check**.

The function saves application's state so that the student can later return to
the application and find it as he or she left it.

The name of the ``setState()`` function must be the value of the ``set_statefn``
attribute of the ``jsinput`` element for the problem.

For example:

.. code-block::  xml

    <customresponse cfn="vglcfn">
        <jsinput set_statefn="JSObject.setState"
            . . . .


====================
getGrade() Function
====================

Your application must contain a ``getGrade()`` function.

The ``getGrade()`` function is executed when the student clicks **Check**. The
``getState()`` function must return the state of objects on which grading is
based as a JSON string.

The JSON string returned by ``getGrade()`` is used by the Python code in the
problem to determine the student's results, as explained below.

The name of the ``getGrade()`` function must be the value of the ``gradefn``
attribute of the ``jsinput`` element for the problem.

For example:

.. code-block::  xml

    <customresponse cfn="vglcfn">
        <jsinput gradefn="JSObject.getGrade"
            . . . .

***************************************
Grade the Student Response with Python
***************************************

To grade a student's interaction with your JavaScript application, you must
write Python code in the problem. When a student clicks **Check**, the Python
code parses the JSON string returned by the application's ``getGrade()``
function and determines if the student's submission is correct or not.

.. note:: Grading for JavaScript applications supports determining if a student's submission is correct or not. You cannot give partial credit with JavaScript applications.

In the Python code, you must:

* Enclose all code in a ``script`` element of type ``loncapa/python``. 

* Import ``json``

* Define a function that is executed when the student clicks Check. This
  function:

  * Is placed before the ``customresponse`` element that defines the problem.
  * By default is named ``vglcfn``
  * Has two parameters:  ``e`` for the submission event, and ``ans``, which is
    the JSON string returned by the JavaScript function ``getGrade()``.
  * Must return ``True`` if the student's submission is correct, or ``False`` if
    it is incorrect.

The structure of the Python code in the problem is:

.. code-block:: xml

    <problem>
        <script type="loncapa/python">
            import json
            def vglcfn(e, ans):
                '''
                Code that parses ans and returns True or False
                '''
        </script>
        <customresponse cfn="vglcfn">
        . . . . 
    </problem>


*******************************************************
XML for Custom JavaScript Applications
*******************************************************

The problem component XML that you define in Studio to provide students with a
JavaScript application has the following structure:

.. code-block::

    <problem>
        <!-- Optional script tag for summative assessments -->
        <script type="loncapa/python">
            import json
            def vglcfn(e, ans):
                '''
                Code that parses ans and returns True or False
                '''
        </script>
        <customresponse cfn="vglcfn">
            <jsinput 
                gradefn="JSObject.getGrade" 
                get_statefn="JSObject.getState" 
                set_statefn="JSObject.setState" 
                width="100%" 
                height="360" 
                html_file="/static/file-name.html" 
                sop="false"/>
        </customresponse>
    </problem>


===================
jsinput attributes
===================

The following table describes the attributes of the ``jsinput`` element.

.. list-table::
   :widths: 10 50 10
   :header-rows: 1

   * - Attribute
     - Description
     - Example
   * - gradefn
     - The function in your JavaScript application that returns the state of the
       objects to be evaluated as a JSON string.
     - ``JSObject.getGrade``
   * - get_statefun
     - The function in your JavaScript application that returns the state of the
       objects.
     - ``JSObject.getState``
   * - set_statefun
     - The function in your JavaScript application that saves the state of the
       objects.
     - ``JSObject.setState``
   * - initial_state
     - A JSON string representing the initial state, if any, of the objects.
     - '{"selectedObjects":{"cube":true,"cylinder":false}}'
   * - width
     - The width of the IFrame in which your JavaScript application will be
       displayed, in pixels.
     - 400
   * - height
     - The height of the IFrame in which your JavaScript application will be
       displayed, in pixels.
     - 400
   * - html_file
     - The name of the HTML file containing your JavaScript application that
       will be loaded in the IFrame.
     - /static/webGLDemo.html
   * - sop
     - The same-origin policy (SOP), meaning that all elements have the same
       protocol, host, and port. To bypass the SOP, set to ``true``.
     - false
