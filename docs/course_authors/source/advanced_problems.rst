.. _Advanced Problems:

Advanced Problems
=================

Advanced problems are problems such as drag and drop, circuit schematic
builder, and math expression problems. These problems appear on the
Advanced tab when you create a new Problem component. Studio provides
templates for these problems, but the problems open directly in the
**Advanced Editor** and have to be created in XML.

-  :ref:`Circuit Schematic Builder` In circuit schematic problems, students
   create and modify circuits on an interactive grid and submit
   computer-generated analyses of the circuits for grading.
-  :ref:`Custom JavaScript Display and Grading` With custom JavaScript display
   and grading problems, you can incorporate problem types that you've created
   in HTML into Studio via an IFrame.
-  :ref:`Write-Your-Own-Grader` Write-your-own-grader problems
   evaluate students' responses using an embedded Python script that you
   create. These problems can be any type.
-  :ref:`Drag and Drop` Drag and drop problems require students to drag text
   or objects to a specific location on an image.
-  :ref:`Image Mapped Input` Image mapped input problems require students to
   click a specific location on an image.
-  :ref:`Math Expression Input` Math expression input problems require
   students to enter a mathematical expression as text, such as
   e=m\*c^2.
-  :ref:`Problem Written in LaTeX` This problem type allows you to convert
   problems that you've already written in LaTeX into the edX format.
   Note that this problem type is still a prototype, however, and may
   not be supported in the future.
-  :ref:`Problem with Adaptive Hint` These problems can give students
   feedback or hints based on their responses. Problems with adaptive
   hints can be text input or multiple choice problems.

These problems are easy to access in Studio. To create them, click
**Problem** under **Add New Component**, click the **Advanced** tab, and
then click the name of the problem that you want to create.

.. _Circuit Schematic Builder:

Circuit Schematic Builder
-------------------------

In circuit schematic builder problems, students can arrange circuit
elements such as voltage sources, capacitors, resistors, and MOSFETs on
an interactive grid. They then submit a DC, AC, or transient analysis of
their circuit to the system for grading.

.. image:: /Images/CircuitSchematicExample.gif

Create a Circuit Schematic Builder Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Circuit Schematic Builder**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

.. _Custom JavaScript Display and Grading:

Custom JavaScript Display and Grading
-------------------------------------

Custom JavaScript display and grading problems (also called custom JavaScript problems or
JS Input problems) allow you to create your own learning tool
using HTML and other standard Internet languages and then add the tool directly
into Studio. When you use this problem type, Studio embeds your tool in an
inline frame (IFrame) so that your students can interact with it in the LMS. You can grade
your students' work using JavaScript and some basic Python, and the grading
is integrated into the edX grading system.

.. image:: /Images/JavaScriptInputExample.gif

Create a Custom JavaScript Display and Grading Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create your JavaScript application, and then upload all files associated with
   that application to the **Files & Uploads** page.
#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Custom JavaScript Display and Grading**.
#. In the component that appears, click **Edit**.
#. In the component editor, modify the example code according to your problem.

   - If some elements of your problem are located in different places, you need to
     bypass the same-origin policy (SOP). To do this, change **sop="false"**
     in line 8 to **sop="true"**. For more information, see
     `same-origin policy <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Same_origin_policy_for_JavaScript>`_.

#. Click the **Settings** tab.
#. Set **Maximum Attempts** to a number larger than zero.
#. Click **Save**.

Re-create the Example Problem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To re-create the example problem above, you'll need the following files.

   - webGLDemo.html
   - webGLDemo.js
   - webGLDemo.css
   - three.min.js

#. Go to :ref:`Appendix F` and use the code samples to create the following files.

   - webGLDemo.html
   - webGLDemo.js
   - webGLDemo.css

#. Download the **three.min.js** file. To do this, go to the `three.js home page <http://threejs.org>`_,
   and then click **Download** in
   the left pane. After the .zip file has finished downloading, open the .zip file, and then
   open the **build** folder to access the three.min.js file.

    **Note** If you need to bypass the SOP, you'll also need the **jschannel.js** file. To do
    this, go to the `jschannel.js <https://github.com/mozilla/jschannel/blob/master/src/jschannel.js>`_
    page, copy the code for the file into a text editor, and then save the file as jschannel.js.

#. On the **Files & Uploads** page, upload all the files you just created or downloaded.
#. Create a new custom JavaScript display and grading problem component.
#. On the **Settings** tab, set **Maximum Attempts** to a number larger than
   zero.
#. In the problem component editor, replace the example code with the code below.
#. Click **Save.**



JavaScript Input Problem Code
#############################

::

    <problem display_name="webGLDemo">
    In the image below, click the cone.

    <script type="loncapa/python">
    import json
    def vglcfn(e, ans):
        '''
        par is a dictionary containing two keys, "answer" and "state"
        The value of answer is the JSON string returned by getGrade
        The value of state is the JSON string returned by getState
        '''
        par = json.loads(ans)
        # We can use either the value of the answer key to grade
        answer = json.loads(par["answer"])
        return answer["cylinder"]  and not answer["cube"]
        # Or we can use the value of the state key
        '''
        state = json.loads(par["state"])
        selectedObjects = state["selectedObjects"]
        return selectedObjects["cylinder"] and not selectedObjects["cube"]
        '''
    </script>
    <customresponse cfn="vglcfn">
        <jsinput
            gradefn="WebGLDemo.getGrade"
            get_statefn="WebGLDemo.getState"
            set_statefn="WebGLDemo.setState"
            width="400"
            height="400"
            html_file="/static/webGLDemo.html"
        />
    </customresponse>
    </problem>


.. note::    When you create this problem, keep the following in mind.

             - The webGLDemo.js file defines the three JavaScript functions (**WebGLDemo.getGrade**,
               **WebGLDemo.getState**, and **WebGLDemo.setState**).

             - The JavaScript input problem code uses **WebGLDemo.getGrade**, **WebGLDemo.getState**,
               and **WebGLDemo.setState** to grade, save, or restore a problem. These functions must
               be global in scope.

             - **WebGLDemo.getState** and **WebGLDemo.setState** are optional. You only have to define
               these functions if you want to conserve the state of the problem.

             - **Width** and **height** represent the dimensions of the IFrame that holds the
               application.

             - When the problem opens, the cone and the cube are both blue, or "unselected." When
               you click either shape once, the shape becomes yellow, or "selected." To unselect
               the shape, click it again. Continue clicking the shape to select and unselect it.

             - The response is graded as correct if the cone is selected (yellow) when the user
               clicks **Check**.

             - Clicking **Check** or **Save** registers the problem's current state.



.. _Write-Your-Own-Grader:

Write-Your-Own-Grader ("Custom Python-Evaluated Input")
-------------------------------------------------------


In write-your-own-grader problems (also called "custom Python-evaluated
input" problems), the grader evaluates a student's response using a
Python script that you create and embed in the problem. These problems
can be any type. Numerical input and text input problems are the most
popular write-your-own-grader.

.. image:: Images/WriteYourOwnGraderExample.gif

Create a Write-Your-Own-Grader Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a write-your-own-grader problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Custom Python-Evaluated Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

For more information about write-your-own-grader problems, see `CustomResponse XML and Python
Script <https://edx.readthedocs.org/en/latest/course_data_formats/custom_response.html>`_.

.. _Drag and Drop:

Drag and Drop
-------------

In drag and drop problems, students respond to a question by dragging
text or objects to a specific location on an image.

.. image:: Images/DragAndDropExample.gif

Create a Drag and Drop Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a drag and drop problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Drag and Drop**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.


For more information about drag and drop problems, see `XML Format of Drag and Drop Input
<http://data.edx.org/en/latest/course_data_formats/drag_and_drop/drag_and_drop_input.html>`_.

.. _Image Mapped Input:

Image Mapped Input
------------------

In an image mapped input problem, students click inside a defined area
in an image. You define this area by including coordinates in the body
of the problem.

.. image:: Images/ImageMappedInputExample.gif

Create an Image Mapped Input Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a image mapped input problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Image Mapped Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.



.. _Math Expression Input:

Math Expression Input
---------------------

In math expression input problems, students enter text that represents
a mathematical expression, and Studio changes that text to a symbolic
expression that appears below the field where the student is typing.
Unlike numerical input problems, which only allow integers and a few
select constants, math expression problems can include more complicated
symbolic expressions.

When you create a math expression input problem for your students in
Studio, you'll use `MathJax <http://www.mathjax.org>`_ to change your
plain text into "beautiful math." For more information about how to use
MathJax in Studio, see :ref:`MathJax in Studio`.

.. image:: Images/MathExpressionInputExample.gif

Create a Math Expression Input Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a math expression input problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Math Expression Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

For more information, see `Symbolic Response
<https://edx.readthedocs.org/en/latest/course_data_formats/symbolic_response.html>`_.

.. _Problem Written in LaTeX:

Problem Written in LaTeX
------------------------

If you have an problem that is already written in LaTeX, you can use
this problem type to easily convert your code into XML. After you paste
your code into the LaTeX editor, you'll only need to make a few minor
adjustments. Note that **this problem type is still a prototype and may
not be supported in the future**, so you should use it with caution.

.. note:: If you want to use LaTeX to typeset mathematical expressions
          in problems that you haven't yet written, use any of the other problem
          templates together with `MathJax <http://www.mathjax.org>`_. For more
          information about how to create mathematical expressions in Studio using
          MathJax, see *A Brief Introduction to MathJax in Studio*.

.. image:: Images/ProblemWrittenInLaTeX.gif

Create a Problem Written in LaTeX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a problem written in LaTeX:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Problem Written in LaTeX**.
#. In the component editor that appears, click **Edit**.
#. In the lower left corner of the component editor, click **Launch
   LaTeX Source Compiler**.
#. Replace the example code with your own code.
#. In the lower left corner of the LaTeX source compiler, click **Save &
   Compile to edX XML**.

.. _Problem with Adaptive Hint:

Problem with Adaptive Hint
--------------------------

A problem with an adaptive hint evaluates a student's response, then
gives the student feedback or a hint based on that response so that the
student is more likely to answer correctly on the next attempt. These
problems can be text input or multiple choice problems.

.. image:: Images/ProblemWithAdaptiveHintExample.gif

Create a Problem with an Adaptive Hint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a problem with an adaptive hint:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Problem with Adaptive Hint**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.
