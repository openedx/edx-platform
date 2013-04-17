####################################
CustomResponse XML and Python Script
####################################

This document explains how to write a CustomResponse problem.  CustomResponse
problems execute Python script to check student answers and provide hints.

There are two general ways to create a CustomResponse problem:


*****************
Answer tag format
*****************
One format puts the Python code in an ``<answer>`` tag:

.. code-block:: xml

    <problem>
        <p>What is the sum of 2 and 3?</p>

        <customresponse expect="5">
        <textline math="1" />
        </customresponse>

        <answer>
    # Python script goes here
        </answer>
    </problem>


The Python script interacts with these variables in the global context:
    * ``answers``: An ordered list of answers the student provided.
      For example, if the student answered ``6``, then ``answers[0]`` would
      equal ``6``.
    * ``expect``: The value of the ``expect`` attribute of ``<customresponse>``
      (if provided).
    * ``correct``: An ordered list of strings indicating whether the
      student answered the question correctly.  Valid values are
      ``"correct"``, ``"incorrect"``, and ``"unknown"``.  You can set these
      values in the script.
    * ``messages``: An ordered list of message strings that will be displayed
      beneath each input.  You can use this to provide hints to users.
      For example ``messages[0] = "The capital of California is Sacramento"``
      would display that message beneath the first input of the response.
    * ``overall_message``: A string that will be displayed beneath the
      entire problem.  You can use this to provide a hint that applies
      to the entire problem rather than a particular input.

Example of a checking script:

.. code-block:: python

    if answers[0] == expect:
        correct[0] = 'correct'
        overall_message = 'Good job!'
    else:
        correct[0] = 'incorrect'
        messages[0] = 'This answer is incorrect'
        overall_message = 'Please try again'

**Important**: Python is picky about indentation.  Within the ``<answer>`` tag,
you must begin your script with no indentation.

*****************
Script tag format
*****************
The other way to create a CustomResponse is to put a "checking function"
in a ``<script>`` tag, then use the ``cfn`` attribute of the
``<customresponse>`` tag:

.. code-block:: xml

    <problem>
        <p>What is the sum of 2 and 3?</p>

        <customresponse cfn="check_func" expect="5">
        <textline math="1" />
        </customresponse>

        <script type="loncapa/python">
    def check_func(expect, ans):
        # Python script goes here
        </script>
    </problem>


**Important**: Python is picky about indentation.  Within the ``<script>`` tag,
the ``def check_func(expect, ans):`` line must have no indentation.

The check function accepts two arguments:
    * ``expect`` is the value of the ``expect`` attribute of ``<customresponse>``
      (if provided)
    * ``answer`` is either:

        * The value of the answer the student provided, if there is only one input.
        * An ordered list of answers the student provided, if there
          are multiple inputs.

There are several ways that the check function can indicate whether the student
succeeded.  The check function can return any of the following:

    * ``True``: Indicates that the student answered correctly for all inputs.
    * ``False``: Indicates that the student answered incorrectly.
      All inputs will be marked incorrect.
    * A dictionary of the form: ``{ 'ok': True, 'msg': 'Message' }``
      If the dictionary's value for ``ok`` is set to ``True``, all inputs are
      marked correct; if it is set to ``False``, all inputs are marked incorrect.
      The ``msg`` is displayed beneath all inputs, and it may contain
      XHTML markup.
    * A dictionary of the form 

.. code-block:: xml
      
    
    { 'overall_message': 'Overall message',
        'input_list': [
            { 'ok': True, 'msg': 'Feedback for input 1'},
            { 'ok': False, 'msg': 'Feedback for input 2'},
            ... ] }

The last form is useful for responses that contain multiple inputs.
It allows you to provide feedback for each input individually,
as well as a message that applies to the entire response.

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

The function checks that the user entered ``1`` for the first input, 
``2`` for the  second input, and ``3`` for the third input.
It provides feedback messages for each individual input, as well
as a message displayed beneath the entire problem.
