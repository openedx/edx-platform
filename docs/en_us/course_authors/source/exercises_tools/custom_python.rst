.. _Write Your Own Grader:

##############################
Write-Your-Own-Grader Problem
##############################

In custom Python-evaluated input (also called "write-your-own-grader" problems), the grader uses a Python script that you create and embed in the problem to evaluates a student's response or provide hints. These problems can be any type. Numerical input and text input problems are the most popular write-your-own-grader problems.

.. image:: /Images/CustomPythonExample.png
 :alt: Image of a write your own grader problem

Custom Python-evaluated input problems can include the following:

* :ref:`Chemical Equation`
* :ref:`Custom JavaScript`
* :ref:`Gene Explorer`
* :ref:`Molecule Editor`
* :ref:`Protein Builder`

.. list-table::
   :widths: 20 80

   * - ``<script type="loncapa/python">``
     - Indicates that the problem contains a Python script.
   * - ``<customresponse cfn="test_add_to_ten">``
     - 
   * - ``<customresponse cfn="test_add" expect="20">``
     - 
   * - <textline size="10" correct_answer="3"/>
     - This tag includes the ``size``, ``correct_answer``, and ``label`` attributes. The ``correct_answer`` attribute is optional.

You can create one of these problems in :ref:`Answer Tag Format` or :ref:`Script Tag Format`.

.. _Answer Tag Format:

**************************
Answer Tag Format
**************************

The answer tag format encloses the Python script in an ``<answer>`` tag:

.. code-block:: xml

  <answer>
  if answers[0] == expect:
      correct[0] = 'correct'
      overall_message = 'Good job!'
  else:
      correct[0] = 'incorrect'
      messages[0] = 'This answer is incorrect'
      overall_message = 'Please try again'
  </answer>

.. important:: Python honors indentation. Within the ``<answer>`` tag, you must begin your script with no indentation.

The Python script interacts with these variables in the global context:

* ``answers``: An ordered list of answers the student provided. For example, if the student answered ``6``, ``answers[0]`` would equal ``6``.
* ``expect``: The value of the ``expect`` attribute of ``<customresponse>`` (if provided).
* ``correct``: An ordered list of strings indicating whether the student answered the question correctly.  Valid values are ``"correct"``, ``"incorrect"``, and ``"unknown"``.  You can set these values in the script.
* ``messages``: An ordered list of messages that appear under each response field in the problem. You can use this to provide hints to users. For example, if you include ``messages[0] = "The capital of California is Sacramento"``, that message appears under the first response field in the problem.
* ``overall_message``: A message that appears beneath the entire problem. You can use this to provide a hint that applies to the entire problem rather than a particular response field.

========================================================================
Create a Custom Python-Evaluated Input Problem in Answer Tag Format
========================================================================

To create a custom Python-evaluated input problem using an ``<answer>`` tag:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Custom Python-Evaluated Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with the following code.
#. Click **Save**.

.. code-block:: xml

    <problem>
        <p>What is the sum of 2 and 3?</p>

        <customresponse expect="5">
        <textline math="1" />
        </customresponse>

        <answer>
    if answers[0] == expect:
        correct[0] = 'correct'
        overall_message = 'Good job!'
    else:
        correct[0] = 'incorrect'
        messages[0] = 'This answer is incorrect'
        overall_message = 'Please try again'
        </answer>
    </problem>

.. important:: Python honors indentation. Within the ``<answer>`` tag, you must begin your script with no indentation.

.. _Script Tag Format:

**************************
Script Tag Format
**************************

The script tag format encloses a Python script that contains a "check function" in a ``<script>`` tag, and adds the ``cfn`` attribute of the ``<customresponse>`` tag to reference that function:

.. code-block:: xml

  <problem>

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

  <p>Enter two integers that sum to 10. </p>
  <customresponse cfn="test_add_to_ten">
          <textline size="10"/><br/>
          <textline size="10"/>
  </customresponse>

  </problem>

**Important**: Python honors indentation. Within the ``<script>`` tag, the ``def check_func(expect, ans):`` line must have no indentation.

The **check** function accepts two arguments:

* ``expect`` is the value of the ``expect`` attribute of ``<customresponse>`` (if provided)
* ``answer`` is either:

    * The value of the answer the student provided, if the problem only has one response field.
    * An ordered list of answers the student provided, if the problem has multiple response fields.

The **check** function can return any of the following to indicate whether the student's answer is correct:

* ``True``: Indicates that the student answered correctly for all response fields.
* ``False``: Indicates that the student answered incorrectly. All response fields are marked as incorrect.
* A dictionary of the form: ``{ 'ok': True, 'msg': 'Message' }``
  If the dictionary's value for ``ok`` is set to ``True``, all response fields are marked correct; if it is set to ``False``, all response fields are marked incorrect. The ``msg`` is displayed beneath all response fields, and it may contain XHTML markup.
* A dictionary of the form 

.. code-block:: xml
      
    
    { 'overall_message': 'Overall message',
        'input_list': [
            { 'ok': True, 'msg': 'Feedback for input 1'},
            { 'ok': False, 'msg': 'Feedback for input 2'},
            ... ] }

The last form is useful for responses that contain multiple response fields. It allows you to provide feedback for each response field individually, as well as a message that applies to the entire response.

Example of a checking function:

.. code-block:: python

    def check_func(expect, answer_given):
        check1 = (int(answer_given[0]) == 1)
        check2 = (int(answer_given[1]) == 2)
        check3 = (int(answer_given[2]) == 3)
        return {'overall_message': 'Overall message',
                    'input_list': [
                        { 'ok': check1, 'msg': 'Feedback 1'},
                        { 'ok': check2, 'msg': 'Feedback 2'},
                        { 'ok': check3, 'msg': 'Feedback 3'} ] }

The function checks that the user entered ``1`` for the first input, ``2`` for the  second input, and ``3`` for the third input. It provides feedback messages for each individual input, as well as a message displayed beneath the entire problem.

========================================================================
Create a Custom Python-Evaluated Input Problem in Script Tag Format
========================================================================

To create a custom Python-evaluated input problem using a ``<script>`` tag:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Custom Python-Evaluated Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with the following code.
#. Click **Save**.

**Problem Code**:

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

