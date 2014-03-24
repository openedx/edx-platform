.. _Advanced Problems:

Advanced Problems
=================

Advanced problems are problems such as drag and drop, circuit schematic
builder, and math expression problems. Many of these problems appear on the
Advanced tab when you create a new Problem component. Studio provides
templates for these problems, but the problems open directly in the
**Advanced Editor** and have to be created in XML.

-  :ref:`Chemical Equation` In chemical equation problems, students enter text that represents a chemical equation into a text box. 
-  :ref:`Circuit Schematic Builder` In circuit schematic problems, students
   create and modify circuits on an interactive grid and submit
   computer-generated analyses of the circuits for grading.
-  :ref:`Custom JavaScript Display and Grading` With custom JavaScript display
   and grading problems, you can incorporate problem types that you've created
   in HTML into Studio via an IFrame.
-  :ref:`Custom Python Evaluated Input` Custom Python-evaluated input (also called "write-your-own-grader" problems evaluate students' responses using an embedded Python script that you create. These problems can be any type.
-  :ref:`Drag and Drop` Drag and drop problems require students to drag text
   or objects to a specific location on an image.
-  :ref:`Image Mapped Input` Image mapped input problems require students to
   click a specific location on an image.
-  :ref:`Math Expression Input` Math expression input problems require
   students to enter a mathematical expression as text, such as
   e=m\*c^2.
-  :ref:`Problem with Adaptive Hint` These problems can give students
   feedback or hints based on their responses. Problems with adaptive
   hints can be text input or multiple choice problems.
- :ref:`Problem Written in LaTeX` This problem type allows you to convert problems that you’ve already written in LaTeX into the edX format. Note that this problem type is still a prototype, however, and may not be supported in the future.

These problems are easy to access in Studio. To create them, click
**Problem** under **Add New Component**, click the **Advanced** tab, and
then click the name of the problem that you want to create.

To add a label for an advanced problem, you'll add a **label** attribute to one of the XML tags for the problem. For more information, see :ref:`Appendix E`.

.. _Chemical Equation Input:

Chemical Equation
-----------------

In chemical equation problems, students enter text that represents a chemical equation into a text box. The LMS converts that text into a chemical equation below the text box.

**Sample Problem**

.. image:: /Images/ChemicalEquationExample.png
 :alt: Image of a chemical equation problem

**Required Tags**

.. list-table::
   :widths: 20 80

   * - ``<customresponse>``
     - Indicates that this problem has a custom response. The ``<customresponse>`` tags must surround the ``<chemicalequation>`` tags.
   * - ``<chemicalequationinput>``
     - A child of ``<customresponse>``. Indicates that the answer to this problem is a chemical equation. Must contain the ``size`` and ``label`` attributes.
   * - ``<answer type=loncapa/python>``
     - A child of ``<chemicalequationinput>``. Contains the Python script that grades the problem.

Chemical equation problems use MathJax to create formulas. For more information about using MathJax in Studio, see :ref:`MathJax in Studio`.

**Sample Problem XML**:

.. code-block:: xml

  <problem>
    <startouttext/>
    <p>Some problems may ask for a particular chemical equation. Practice by writing out the following reaction in the box below.</p>
    
  \( \text{H}_2\text{SO}_4 \longrightarrow \text { H}^+ + \text{ HSO}_4^-\)

    <customresponse>
      <chemicalequationinput size="50" label="Practice by writing out the following reaction in the box below."/>
      <answer type="loncapa/python">

  if chemcalc.chemical_equations_equal(submission[0], 'H2SO4 -> H^+ + HSO4^-'):
      correct = ['correct']
  else:
      correct = ['incorrect']

      </answer>
    </customresponse>
    <p>Some tips:</p>
    <ul>
    <li>Use real element symbols.</li>
    <li>Create subscripts by using plain text.</li>
    <li>Create superscripts by using a caret (^).</li>
    <li>Create the reaction arrow (\(\longrightarrow\)) by using "->".</li>
    </ul>

    <endouttext/>
  
   <solution>
   <div class="detailed-solution">
   <p>Solution</p>
   <p>To create this equation, enter the following:</p>
     <p>H2SO4 -> H^+ + HSO4^-</p>
   </div>
   </solution>
  </problem>

**Problem Template**:

.. code-block:: xml

  <problem>
    <startouttext/>
    <p>Problem text</p>

    <customresponse>
      <chemicalequationinput size="50" label="label text"/>
      <answer type="loncapa/python">

  if chemcalc.chemical_equations_equal(submission[0], 'TEXT REPRESENTING CHEMICAL EQUATION'):
      correct = ['correct']
  else:
      correct = ['incorrect']

      </answer>
    </customresponse>

    <endouttext/>
  
   <solution>
   <div class="detailed-solution">
   <p>Solution or Explanation Header</p>
   <p>Solution or explanation text</p>
   </div>
   </solution>
  </problem>


.. _Circuit Schematic Builder:

Circuit Schematic Builder
-------------------------

In circuit schematic builder problems, students can arrange circuit
elements such as voltage sources, capacitors, resistors, and MOSFETs on
an interactive grid. They then submit a DC, AC, or transient analysis of
their circuit to the system for grading.

.. image:: /Images/CircuitSchematicExample.gif
 :alt: Image of a circuit schematic builder

Create a Circuit Schematic Builder Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Circuit Schematic Builder**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

**Problem Code**:

.. code-block:: xml


    <problem>
      <p>Make a voltage divider that splits the provided voltage evenly.</p>
    <schematicresponse>
    <center>
    <schematic height="500" width="600" parts="g,r" analyses="dc"
    initial_value="[["v",[168,144,0],{"value":"dc(1)","_json_":0},["1","0"]],["r",[296,120,0],{"r":"1","_json_":1},["1","output"]],["L",[296,168,3],{"label":"output","_json_":2},["output"]],["w",[296,216,168,216]],["w",[168,216,168,192]],["w",[168,144,168,120]],["w",[168,120,296,120]],["g",[168,216,0],{"_json_":7},["0"]],["view",-67.49999999999994,-78.49999999999994,1.6000000000000003,"50","10","1G",null,"100","1","1000"]]"
    />
    </center>
    <answer type="loncapa/python">
    dc_value = "dc analysis not found"
    for response in submission[0]:
      if response[0] == 'dc':
          for node in response[1:]:
              dc_value = node['output']
    if dc_value == .5:
      correct = ['correct']
    else:
      correct = ['incorrect']
    </answer>
    </schematicresponse>
    <schematicresponse>
    <p>Make a high pass filter.</p>
    <center>
    <schematic height="500" width="600" parts="g,r,s,c" analyses="ac"
    submit_analyses="{"ac":[["NodeA",1,9]]}"
    initial_value="[["v",[160,152,0],{"name":"v1","value":"sin(0,1,1,0,0)","_json_":0},["1","0"]],["w",[160,200,240,200]],["g",[160,200,0],{"_json_":2},["0"]],["L",[240,152,3],{"label":"NodeA","_json_":3},["NodeA"]],["s",[240,152,0],{"color":"cyan","offset":"0","_json_":4},["NodeA"]],["view",64.55878906250004,54.114697265625054,2.5000000000000004,"50","10","1G",null,"100","1","1000"]]"/>
    </center>
    <answer type="loncapa/python">
    ac_values = None
    for response in submission[0]:
      if response[0] == 'ac':
          for node in response[1:]:
              ac_values = node['NodeA']
    print "the ac analysis value:", ac_values
    if ac_values == None:
      correct = ['incorrect']
    elif ac_values[0][1] < ac_values[1][1]:
      correct = ['correct']
    else:
      correct = ['incorrect']
    </answer>
    </schematicresponse>
        <solution>
            <div class="detailed-solution">
                <p>Explanation</p>
                <p>A voltage divider that evenly divides the input voltage can be formed with two identically valued resistors, with the sampled voltage taken in between the two.</p>
                <p><img src="/c4x/edX/edX101/asset/images_voltage_divider.png"/></p>
                <p>A simple high-pass filter without any further constaints can be formed by simply putting a resister in series with a capacitor. The actual values of the components do not really matter in order to meet the constraints of the problem.</p>
                <p><img src="/c4x/edX/edX101/asset/images_high_pass_filter.png"/></p>
            </div>
        </solution>
    </problem>

.. _Custom JavaScript Display and Grading:

Custom JavaScript Display and Grading
-------------------------------------

Custom JavaScript display and grading problems (also called custom JavaScript problems
or JS Input problems) allow you to create a custom problem or tool that uses JavaScript
and then add the problem or tool directly into Studio. When you create a JS Input problem,
Studio embeds the problem in an inline frame (IFrame) so that your students can interact with
it in the LMS. You can grade your students’ work using JavaScript and some basic Python, and
the grading is integrated into the edX grading system.

The JS Input problem that you create must use HTML, JavaScript, and cascading style sheets
(CSS). You can use any application creation tool, such as the Google Web Toolkit (GWT), to
create your JS Input problem.

.. image:: /Images/JavaScriptInputExample.gif
 :alt: Image of a JavaScript Input problem

Create a Custom JavaScript Display and Grading Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create your JavaScript application, and then upload all files associated with
   that application to the **Files & Uploads** page.
#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Custom JavaScript Display and Grading**.
#. In the component that appears, click **Edit**.
#. In the component editor, modify the example code according to your problem.

   - All problems have more than one element. Most problems conform to the same-origin
     policy (SOP), meaning that all elements have the same protocol, host, and port.
     For example, **http**://**store.company.com**:**81**/subdirectory_1/JSInputElement.html and
     **http**://**store.company.com**:**81**/subdirectory_2/JSInputElement.js have the same protocol
     (http), host (store.company.com), and port (81).

     If any elements of your problem use a different protocol, host, or port, you need to
     bypass the SOP. For example, **https**://**info.company.com**/JSInputElement2.html
     uses a different protocol, host, and port. To bypass the SOP, change
     **sop="false"** in line 8 of the example code to **sop="true"**. For more information, see the same-origin policy
     page on the `Mozilla Developer Network <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Same_origin_policy_for_JavaScript>`_
     or on `Wikipedia <http://en.wikipedia.org/wiki/Same_origin_policy>`_.
#. If you want your problem to have a **Save** button, click the **Settings** tab, and then set
   **Maximum Attempts** to a number larger than zero.
#. Click **Save**.

Re-create the Example Problem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To re-create the example problem above, you'll need the following files.

   - webGLDemo.html
   - webGLDemo.js
   - webGLDemo.css
   - three.min.js

You'll create the first three files using the code in :ref:`Appendix F`. The three.min.js file is a library
file that you'll download.

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

             - The webGLDemo.js file defines the three JavaScript functions (**WebGLDemo.getGrade**, **WebGLDemo.getState**, and **WebGLDemo.setState**).

             - The JavaScript input problem code uses **WebGLDemo.getGrade**, **WebGLDemo.getState**, and **WebGLDemo.setState** to grade, save, or restore a problem. These functions must be global in scope.

             - **WebGLDemo.getState** and **WebGLDemo.setState** are optional. You only have to define these functions if you want to conserve the state of the problem.

             - **Width** and **height** represent the dimensions of the IFrame that holds the application.

             - When the problem opens, the cone and the cube are both blue, or "unselected." When you click either shape once, the shape becomes yellow, or "selected." To unselect the shape, click it again. Continue clicking the shape to select and unselect it.

             - The response is graded as correct if the cone is selected (yellow) when the user clicks **Check**.

             - Clicking **Check** or **Save** registers the problem's current state.



.. _Custom Python Evaluated Input:

Custom Python-Evaluated Input ("Write-Your-Own-Grader")
-------------------------------------------------------


In custom Python-evaluated input  (also called "write-your-own-grader problems" problems), the grader evaluates a student's response using a Python script that you create and embed in the problem. These problems can be any type. Numerical input and text input problems are the most popular write-your-own-grader problems.

.. image:: Images/CustomPythonExample.png
 :alt: Image of a write your own grader problem

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

**Sample Problem XML**:

.. code-block:: xml

  <problem>
  <p>This question has two parts.</p>

  <script type="loncapa/python">

  def test_add(expect, ans):
      try:
          a1=int(ans[0])
          a2=int(ans[1])
          return (a1+a2) == int(expect)
      except ValueError:
          return False

  def test_add_to_ten(expect, ans):
      return test_add(10, ans)

  </script>

  <p>Part 1: Enter two integers that sum to 10. </p>
  <customresponse cfn="test_add_to_ten">
          <textline size="10" correct_answer="3" label="Integer #1"/><br/>
          <textline size="10" correct_answer="7" label="Integer #2"/>
  </customresponse>

  <p>Part 2: Enter two integers that sum to 20. </p>
  <customresponse cfn="test_add" expect="20">
          <textline size="10" label="Integer #1"/><br/>
          <textline size="10" label="Integer #2"/>
  </customresponse>

  <solution>
      <div class="detailed-solution">
          <p>Explanation</p>
          <p>For part 1, any two numbers of the form <i>n</i> and <i>10-n</i>, where <i>n</i> is any integer, will work. One possible answer would be the pair 0 and 10.</p>
          <p>For part 2, any pair <i>x</i> and <i>20-x</i> will work, where <i>x</i> is any real number with a finite decimal representation. Both inputs have to be entered either in standard decimal notation or in scientific exponential notation. One possible answer would be the pair 0.5 and 19.5. Another way to write this would be 5e-1 and 1.95e1.</p>
      </div>
  </solution>
  </problem>

**Templates**

The following template includes answers that appear when the student clicks **Show Answer**. 

.. code-block:: xml

  <problem>

  <script type="loncapa/python">
  def test_add(expect,ans):
    a1=float(ans[0])
    a2=float(ans[1])
    return (a1+a2)== float(expect)
  </script>


  <p>Problem text</p>
  <customresponse cfn="test_add" expect="20">
          <textline size="10" correct_answer="11" label="Integer #1"/><br/>
          <textline size="10" correct_answer="9" label="Integer #2"/>
  </customresponse>

      <solution>
          <div class="detailed-solution">
            <p>Solution or Explanation Heading</p>
            <p>Solution or explanation text</p>
          </div>
      </solution>
  </problem>

The following template does not return answers when the student clicks **Show Answer**. If your problem doesn't include answers for the student to see, make sure to set **Show Answer** to **Never** in the problem component.

.. code-block:: xml

  <problem>

  <script type="loncapa/python">
  def test_add(expect,ans):
    a1=float(ans[0])
    a2=float(ans[1])
    return (a1+a2)== float(expect)
  </script>


  <p>Enter two real numbers that sum to 20: </p>
  <customresponse cfn="test_add" expect="20">
          <textline size="10"  label="Integer #1"/><br/>
          <textline size="10"  label="Integer #2"/>
  </customresponse>

      <solution>
          <div class="detailed-solution">
            <p>Solution or Explanation Heading</p>
            <p>Solution or explanation text</p>
          </div>
      </solution>
  </problem>

.. _Drag and Drop:

Drag and Drop
-------------

In drag and drop problems, students respond to a question by dragging
text or objects to a specific location on an image.

.. image:: Images/DragAndDropProblem.png
 :alt: Image of a drag and drop problem

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
<https://edx.readthedocs.org/en/latest/course_data_formats/drag_and_drop/drag_and_drop_input.html>`_.

.. _Image Mapped Input:

Image Mapped Input
------------------

In an image mapped input problem, students click inside a defined area
in an image. You define this area by including coordinates in the body
of the problem.

.. image:: Images/ImageMappedInputExample.gif
 :alt: Image of an image mapped input problem

Create an Image Mapped Input Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a image mapped input problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Image Mapped Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

**Problem Code**:

.. code-block:: xml

  <problem>
    <p><b>Example Problem</b></p>
     <startouttext/>
      <p>In the image below, click the triangle.</p>
      <endouttext/>
      <imageresponse>
      <imageinput src="/static/threeshapes.png" width="220" height="150" rectangle="(80,40)-(130,90)" />
      </imageresponse>
  </problem>

**Problem Template**

.. code-block:: xml

  <problem>
    <startouttext/>
      <p>In the image below, click the triangle.</p>
    <endouttext/>
        <imageresponse>
         <imageinput src="IMAGE FILE PATH" width="NUMBER" height="NUMBER" rectangle="(X-AXIS,Y-AXIS)-(X-AXIS,Y-AXIS)" />
        </imageresponse>
  </problem>

.. _Math Expression Input:

Math Expression Input
---------------------

In math expression input problems, students enter text that represents a mathematical expression into a field, and the LMS changes that text to a symbolic expression that appears below that field. 

.. image:: Images/MathExpressionInputExample.gif
 :alt: Image of math expression input problem

Unlike numerical input problems, which only allow integers and a few select constants, math expression problems can include unknown variables and more complicated symbolic expressions. The grader uses a numerical sampling to determine whether the student's response matches the instructor-provided math expression, to a specified numerical tolerance. The instructor must specify the allowed variables in the expression as well as the range of values for each variable.

.. warning:: Math expression input problems cannot currently include negative numbers raised to fractional powers, such as (-1)^(1/2). Math expression input problems can include complex numbers raised to fractional powers, or positive non-complex numbers raised to fractional powers.

When you create a math expression input problem in Studio, you'll use `MathJax <http://www.mathjax.org>`_ to change your plain text into "beautiful math." For more information about how to use MathJax in Studio, see :ref:`MathJax in Studio`.

**Notes for Students**

When you answer a math expression input problem, follow these guidelines.

* Use standard arithmetic operation symbols.
* Indicate multiplication explicitly by using an asterisk (*).
* Use a caret (^) to raise to a power.
* Use an underscore (_) to indicate a subscript.
* Use parentheses to specify the order of operations.

The LMS automatically converts the following Greek letter names into the corresponding Greek characters when a student types them in the answer field:

.. list-table::
   :widths: 20 20 20 20
   :header-rows: 0

   * - alpha
     - beta
     - gamma
     - delta
   * - epsilon
     - varepsilon
     - zeta
     - eta
   * - theta
     - vartheta
     - iota
     - kappa
   * - lambda
     - mu
     - nu
     - xi
   * - pi
     - rho
     - sigma
     - tau
   * - upsilon
     - phi
     - varphi
     - chi
   * - psi
     - omega
     - 
     - 

note:: ``epsilon`` is the lunate version, whereas ``varepsilon`` looks like a backward 3.

Create a Math Expression Input Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a math expression input problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Math Expression Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - ``<formularesponse>``
     - 
   * - ``<formulaequationinput>``
     - This tag includes the ``size`` and ``label`` attributes.
   * - ``<script type="loncapa/python">``
     - 

**Sample Problem XML**

.. code-block:: xml

  <problem>
    <p>Some problems may ask for a mathematical expression. Practice creating mathematical expressions by answering the questions below.</p>

    <p>Write an expression for the product of R_1, R_2, and the inverse of R_3.</p>
    <formularesponse type="ci" samples="R_1,R_2,R_3@1,2,3:3,4,5#10" answer="$VoVi">
      <responseparam type="tolerance" default="0.00001"/>
      <formulaequationinput size="40" label="Enter the equation"/>
    </formularesponse>

  <script type="loncapa/python">
  VoVi = "(R_1*R_2)/R_3"
  </script>

    <p>Let <i>x</i> be a variable, and let <i>n</i> be an arbitrary constant. What is the derivative of <i>x<sup>n</sup></i>?</p>
  <script type="loncapa/python">
  derivative = "n*x^(n-1)"
  </script>
    <formularesponse type="ci" samples="x,n@1,2:3,4#10" answer="$derivative">
      <responseparam type="tolerance" default="0.00001"/>
      <formulaequationinput size="40"  label="Enter the equation"/>
    </formularesponse>

    <solution>
      <div class="detailed-solution">
        <p>Explanation or Solution Header</p>
        <p>Explanation or solution text</p>
      </div>
    </solution>
  </problem>

**Template XML**

.. code-block:: xml

  <problem>
    <p>Problem text</p>
    <formularesponse type="ci" samples="VARIABLES@LOWER_BOUNDS:UPPER_BOUNDS#NUMBER_OF_SAMPLES" answer="$VoVi">
      <responseparam type="tolerance" default="0.00001"/>
      <formulaequationinput size="20"  label="Enter the equation"/>
    </formularesponse>

  <script type="loncapa/python">
  VoVi = "(R_1*R_2)/R_3"
  </script>

    <solution>
      <div class="detailed-solution">
        <p>Explanation or Solution Header</p>
        <p>Explanation or solution text</p>
      </div>
    </solution>
  </problem>



For more information, see `Symbolic Response
<https://edx.readthedocs.org/en/latest/course_data_formats/symbolic_response.html>`_.

.. _Problem with Adaptive Hint:

Problem with Adaptive Hint
--------------------------

A problem with an adaptive hint evaluates a student's response, then
gives the student feedback or a hint based on that response so that the
student is more likely to answer correctly on the next attempt. These
problems can be text input or multiple choice problems.

.. image:: Images/ProblemWithAdaptiveHintExample.gif
 :alt: Image of a problem with an adaptive hint

Create a Problem with an Adaptive Hint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a problem with an adaptive hint:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Problem with Adaptive Hint**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

.. _Problem Written in LaTeX:

Problem Written in LaTeX
------------------------

.. warning:: This problem type is still a prototype and may not be supported in the future. By default, the ability to create these problems is not enabled in Studio. You must change the advanced settings in your course before you can create problems with LaTeX. Use this problem type with caution.

If you have an problem that is already written in LaTeX, you can use
this problem type to easily convert your code into XML. After you paste
your code into the LaTeX editor, you'll only need to make a few minor
adjustments. 

.. note:: If you want to use LaTeX to typeset mathematical expressions
          in problems that you haven't yet written, use any of the other problem
          templates together with `MathJax <http://www.mathjax.org>`_. For more
          information about how to create mathematical expressions in Studio using
          MathJax, see *A Brief Introduction to MathJax in Studio*.

.. image:: Images/ProblemWrittenInLaTeX.gif
 :alt: Image of a problem written in LaTeX

Create a Problem Written in LaTeX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a problem written in LaTeX:

#. Enable the policy key in your course.

   #. In Studio, click **Settings**, and then click **Advanced Settings**.
   #. On the **Advanced Settings** page, scroll down to the **use_latex_compiler** policy key.
   #. In the **Policy Value** field next to the **use_latex_compiler** policy key, change **false** to **true**.
   #. At the bottom of the page, click **Save Changes**.
   
#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Problem Written in LaTeX**.
#. In the component editor that appears, click **Edit**.
#. In the lower left corner of the component editor, click **Launch
   LaTeX Source Compiler**.
#. Replace the example code with your own code. You can also upload a Latex file into the editor from your computer by clicking **Upload** in the bottom right corner.
#. In the lower left corner of the LaTeX source compiler, click **Save &
   Compile to edX XML**.