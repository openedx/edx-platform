.. _Common Problems:

###############
Common Problems
###############

*Common problems* are typical problems such as multiple choice problems and other problems whose answers are simple for students to select or enter. You can create all of these problems using the Simple Editor in Studio. You don't have to use XML or switch to the Advanced Editor. (However, this section also provides sample XML code for these problems in the Advanced Editor.)

The following are the common problem types in Studio:

-  :ref:`Checkbox` In checkbox problems, students select one or more options
   from a list of possible answers.
-  :ref:`Dropdown` In dropdown problems, students select one answer from a
   dropdown list.
-  :ref:`Multiple Choice` Multiple choice problems require students to
   select one answer from a list of choices that appear directly below
   the question.
-  :ref:`Numerical Input` Numerical input problems require answers that
   include only integers, fractions, and a few common constants and
   operators.
-  :ref:`Text Input` In text input problems, students enter a short text
   answer to a question.

These problems are easy to access in Studio. To create them, click
**Problem** under **Add New Component**, click the **Common Problem
Types** tab, and then click the name of the problem. 

.. note:: All problems must include labels for accessibility. The label generally includes the text of the main question in your problem. To add a label for a common problem, surround the text of the label with angle brackets pointed toward the text (>>*label text*<<).

.. _Checkbox:

*******************
Checkbox
*******************

In checkbox problems, the student selects one or more options from a
list of possible answers. The student must select all the options that
apply to answer the problem correctly. Each checkbox problem must have
at least one correct answer.

.. image:: ../Images/CheckboxExample.png
 :alt: Image of a checkbox problem

==========================
Create a Checkbox Problem
==========================

You can create checkbox problems in the Simple Editor or in the Advanced Editor.

++++++++++++++++++++++++++++++++++++++++++
Simple Editor
++++++++++++++++++++++++++++++++++++++++++

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Checkboxes** on the **Common Problem Types** tab.
#. In the Problem component that appears, click **Edit**.
#. In the component editor, replace the default text with the text of your 
   problem. Enter each answer option on its own line.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select all the answer options, and then click the checkbox button. 

   .. image:: ../Images/ProbComponent_CheckboxIcon.png
    :alt: Image of the checkbox button
   
   When you do this, brackets appear next to each answer choice.

#. Add an **x** between the brackets for the correct answer or answers.
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: ../Images/ProbCompButton_Explanation.png
    :alt: Image of the explanation button

#. On the **Settings** tab, specify the settings that you want. 
#. Click **Save**.

For the example problem above, the text in the Problem component is the
following.

.. code-block:: xml

    Learning about the benefits of preventative healthcare can be particularly 
    difficult. >>Check all of the reasons below why this may be the case.<<

    [x] A large amount of time passes between undertaking a preventative measure and seeing the result. 
    [ ] Non-immunized people will always fall sick. 
    [x] If others are immunized, fewer people will fall sick regardless of a particular individual's choice to get immunized or not. 
    [x] Trust in healthcare professionals and government officials is fragile. 

    [explanation]
    People who are not immunized against a disease may still not fall sick from the disease. If someone is trying to learn whether or not preventative measures against the disease have any impact, he or she may see these people and conclude, since they have remained healthy despite not being immunized, that immunizations have no effect. Consequently, he or she would tend to believe that immunization 
    (or other preventative measures) have fewer benefits than they actually do.
    [explanation]

++++++++++++++++++++++++++++++++++++++++++
Advanced Editor
++++++++++++++++++++++++++++++++++++++++++

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

.. code-block:: xml

  <problem>
  <startouttext/>
    <p>Learning about the benefits of preventative healthcare can be particularly difficult. Check all of the reasons below why this may be the case.</p>

  <choiceresponse>
    <checkboxgroup direction="vertical" label="Check all of the reasons below why this may be the case">
      <choice correct="true"><text>A large amount of time passes between undertaking a preventative measure and seeing the result.</text></choice>
      <choice correct="false"><text>Non-immunized people will always fall sick.</text></choice>
      <choice correct="true"><text>If others are immunized, fewer people will fall sick regardless of a particular individual's choice to get immunized or not.</text></choice>
      <choice correct="true"><text>Trust in healthcare professionals and government officials is fragile.</text></choice>
    </checkboxgroup>

   <solution>
   <div class="detailed-solution">
   <p>Explanation</p>
   <p>People who are not immunized against a disease may still not fall sick from the disease. If someone is trying to learn whether or not preventative measures against the disease have any impact, he or she may see these people and conclude, since they have remained healthy despite not being immunized, that immunizations have no effect. Consequently, he or she would tend to believe that immunization (or other preventative measures) have fewer benefits than they actually do.</p>
   </div>
   </solution>
  </choiceresponse>
  </problem>



.. _Dropdown:

*******************
Dropdown
*******************

Dropdown problems allow the student to choose from a collection of
answer options, presented as a dropdown list. Unlike multiple choice
problems, whose answers are always visible directly below the question,
dropdown problems don't show answer choices until the student clicks
the dropdown arrow.

.. image:: ../Images/DropdownExample.png
 :alt: Image of a dropdown problem

==========================
Create a Dropdown Problem
==========================

You can create dropdown problems in the Simple Editor or in the Advanced Editor.

++++++++++++++++++++++++++++++++++++++++++
Simple Editor
++++++++++++++++++++++++++++++++++++++++++

To create a dropdown problem, follow these steps.

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click
   **Dropdown** on the **Common Problem Types** tab.
#. In the new Problem component that appears, click **Edit**.
#. Replace the default text with the text for your problem. Enter each of the possible 
   answers on the same line, separated by commas.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select all the answer options, and then click the dropdown button. 
      
   .. image:: ../Images/ProbCompButton_Dropdown.png
    :alt: Image of the dropdown button
      
   When you do this, a double set of brackets ([[ ]]) appears and surrounds the 
   answer options.
      
#. Inside the brackets, surround the correct answer with parentheses.
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: ../Images/ProbCompButton_Explanation.png
    :alt: Image of the explanation button

#. On the **Settings** tab, specify the settings that you want. 
#. Click **Save**.

For the example problem above, the text in the Problem component is the
following.

::

    >>What type of data are the following?<<

    Age:
    [[Nominal, Discrete, (Continuous)]]
    Age, rounded to the nearest year:
    [[Nominal, (Discrete), Continuous]]
    Life stage - infant, child, and adult:
    [[(Nominal), Discrete, Continuous]]

++++++++++++++++++++++++++++++++++++++++++
Advanced Editor
++++++++++++++++++++++++++++++++++++++++++

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

**Problem Code:**

.. code-block:: xml

  <problem>
  <p>
    <em>This exercise first appeared in HarvardX's PH207x Health in Numbers: Quantitative Methods in Clinical &amp; Public Health Research course, fall 2012.</em>
  </p>
  <p>What type of data are the following?</p>
  <p>Age:</p>
  <optionresponse>
    <optioninput options="('Nominal','Discrete','Continuous')" correct="Continuous" label="Age"/>
  </optionresponse>
  <p>Age, rounded to the nearest year:</p>
  <optionresponse>
    <optioninput options="('Nominal','Discrete','Continuous')" correct="Discrete" label="Age, rounded to the nearest year"/>
  </optionresponse>
  <p>Life stage - infant, child, and adult:</p>
  <optionresponse>
    <optioninput options="('Nominal','Discrete','Continuous')" correct="Nominal" label="Life stage"/>
  </optionresponse>
  </problem>

.. _Multiple Choice:

*******************
Multiple Choice
*******************

In multiple choice problems, students select one option from a list of
answer options. Unlike with dropdown problems, whose answer choices
don't appear until the student clicks the drop-down arrow, answer
choices for multiple choice problems are always visible directly below
the question.

.. image:: ../Images/MultipleChoiceExample.png
 :alt: Image of a multiple choice problem

You can also configure the following:

* :ref:`Shuffle Answers in a Multiple Choice Problem`
* :ref:`Targeted Feedback in a Multiple Choice Problem`
* :ref:`Answer Pools in a Multiple Choice Problem`

==================================
Create a Multiple Choice Problem
==================================

You can create multiple choice problems in the Simple Editor or in the Advanced Editor.

++++++++++++++++++++++++++++++++++++++++++
Simple Editor
++++++++++++++++++++++++++++++++++++++++++

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Multiple
   Choice** on the **Common Problem Types** tab.
#. When the new Problem component appears, click **Edit**.
#. In the component editor, replace the sample problem text with the text of your 
   problem. Enter each answer option on its own line.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select all the answer options, and then click the multiple choice button. 
   
   .. image:: ../Images/ProbCompButton_MultChoice.png
    :alt: Image of the multiple choice button
   
   When you do this, the component editor adds a pair of parentheses next to each 
   possible answer.
   
#. Add an "x" between the parentheses next to the correct answer.
   
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: ../Images/ProbCompButton_Explanation.png
    :alt: Image of the explanation button

#. On the **Settings** tab, specify the settings that you want. 
#. Click **Save**.

For the example problem above, the text in the Problem component is the
following.

::

    >>Lateral inhibition, as was first discovered in the horsehoe crab:<<

    ( ) is a property of touch sensation, referring to the ability of crabs to 
    detect nearby predators.
    ( ) is a property of hearing, referring to the ability of crabs to detect 
    low frequency noises.
    (x) is a property of vision, referring to the ability of crabs eyes to 
    enhance contrasts.
    ( ) has to do with the ability of crabs to use sonar to detect fellow horseshoe 
    crabs nearby.
    ( ) has to do with a weighting system in the crabs skeleton that allows it to 
    balance in turbulent water.

    [Explanation]
    Horseshoe crabs were essential to the discovery of lateral inhibition, a property of 
    vision present in horseshoe crabs as well as humans, that enables enhancement of 
    contrast at edges of objects as was demonstrated in class. In 1967, Haldan Hartline 
    received the Nobel prize for his research on vision and in particular his research 
    investigating lateral inhibition using horseshoe crabs.
    [Explanation]

++++++++++++++++++++++++++++++++++++++++++
Advanced Editor
++++++++++++++++++++++++++++++++++++++++++

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

.. code-block:: xml

  <problem>
  <p>Lateral inhibition, as was first discovered in the horsehoe crab...</p>
  <multiplechoiceresponse>
    <choicegroup type="MultipleChoice" label="Lateral inhibition, as was first discovered in the horsehoe crab">
      <choice correct="false">is a property of touch sensation, referring to the ability of crabs to detect nearby predators.</choice>
      <choice correct="false">is a property of hearing, referring to the ability of crabs to detect low frequency noises.</choice>
      <choice correct="false">is a property of vision, referring to the ability of crabs eyes to enhance contrasts.</choice>
      <choice correct="true">has to do with the ability of crabs to use sonar to detect fellow horseshoe crabs nearby.</choice>
      <choice correct="false">has to do with a weighting system in the crabs skeleton that allows it to balance in turbulent water.</choice>
    </choicegroup>
  </multiplechoiceresponse>
  <solution>
    <div class="detailed-solution">
      <p>Explanation</p>
      <p>Horseshoe crabs were essential to the discovery of lateral inhibition, a property of vision present in horseshoe crabs as well as humans, that enables enhancement of contrast at edges of objects as was demonstrated in class. In 1967, Haldan Hartline received the Nobel prize for his research on vision and in particular his research investigating lateral inhibition using horseshoe crabs.</p>
    </div>
  </solution>
  </problem>

.. _Shuffle Answers in a Multiple Choice Problem:

=============================================
Shuffle Answers in a Multiple Choice Problem
============================================= 

Optionally, you can configure a multiple choice problem so that it shuffles the order of possible answers.

For example, one view of the problem could be:

.. image:: ../Images/multiple-choice-shuffle-1.png
 :alt: Image of a multiple choice problem

And another view of the same problem, for another student or for the same student of a subsequent view of the unit, could be:

.. image:: ../Images/multiple-choice-shuffle-2.png
 :alt: Image of a multiple choice problem with shuffled answers

You can also have some answers shuffled, but not others. For example, you may want to have the answer "All of the Above" fixed at the end of the list, but shuffle other answers.

You can configure the problem to shuffle answers through :ref:`Simple Editor` or :ref:`Advanced Editor`.

++++++++++++++++++++++++++++++++++++++++++
Use the Simple Editor to Shuffle Answers
++++++++++++++++++++++++++++++++++++++++++

You can configure the problem to shuffle answers in :ref:`Simple Editor`.

For example, the following text defines a multiple choice problem, before shuffling is enabled. The ``(x)`` indicates the correct answer::

 >>What Apple device competed with the portable CD player?<<
     ( ) The iPad
     ( ) Napster
     (x) The iPod
     ( ) The vegetable peeler

To add shuffling to this problem, add ``!`` in the parenthesis of the first answer::

 >>What Apple device competed with the portable CD player?<<
     (!) The iPad
     ( ) Napster
     (x) The iPod
     ( ) The vegetable peeler

To fix an answer's location in the list, add ``@`` in the parenthesis of that answer::

 >>What Apple device competed with the portable CD player?<<
     (!) The iPad
     ( ) Napster
     (x) The iPod
     ( ) The vegetable peeler
     (@) All of the above

You can combine symbols within parenthesis as necessary. For example, to show the correct answer in a fixed location, you could use::
 
  (x@) The iPod

++++++++++++++++++++++++++++++++++++++++++
Use the Advanced Editor to Shuffle Answers
++++++++++++++++++++++++++++++++++++++++++

You can configure the problem to shuffle answers through XML in :ref:`Advanced Editor`.

For example, the following XML defines a multiple choice problem, before shuffling is enabled:

.. code-block:: xml

 <p>What Apple device competed with the portable CD player?</p>
 <multiplechoiceresponse>
  <choicegroup type="MultipleChoice">
    <choice correct="false">The iPad</choice>
    <choice correct="false">Napster</choice>
    <choice correct="true">The iPod</choice>
    <choice correct="false">The vegetable peeler</choice>
  </choicegroup>
 </multiplechoiceresponse>


To add shuffling to this problem, add ``shuffle="true"`` to the ``<choicegroup>`` element:

.. code-block:: xml

 <p>What Apple device competed with the portable CD player?</p>
 <multiplechoiceresponse>
  <choicegroup type="MultipleChoice" shuffle="true">
    <choice correct="false">The iPad</choice>
    <choice correct="false">Napster</choice>
    <choice correct="true">The iPod</choice>
    <choice correct="false">The vegetable peeler</choice>
  </choicegroup>
 </multiplechoiceresponse>

To fix an answer's location in the list, add ``fixed="true"`` to the ``choice`` element for the answer:

.. code-block:: xml

 <p>What Apple device competed with the portable CD player?</p>
 <multiplechoiceresponse>
  <choicegroup type="MultipleChoice" shuffle="true">
    <choice correct="false">The iPad</choice>
    <choice correct="false">Napster</choice>
    <choice correct="true">The iPod</choice>
    <choice correct="false">The vegetable peeler</choice>
    <choice correct="false" fixed="true">All of the above</choice>
  </choicegroup>
 </multiplechoiceresponse>


.. _Targeted Feedback in a Multiple Choice Problem:

===============================================
Targeted Feedback in a Multiple Choice Problem
===============================================

You can configure a multiple choice problem so that explanations for incorrect answers are automatically shown to students.  You can use these explanations to guide students towards the right answer.  Therefore, targeted feedback is most useful for multiple choice problems for which students are allowed multiple attempts.


++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Use the Advanced Editor to Configure Targeted Feedback
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You configure the problem to provide targeted feedback through XML in :ref:`Advanced Editor`.

Follow these XML guidelines:

* Add a ``targeted-feedback`` attribute to the ``<multiplechoiceresponse>`` element, with no value: ``<multiplechoiceresponse targeted-feedback="">``
* Add a ``<targetedfeedbackset>`` element before the ``<solution>`` element.
* Within ``<targetedfeedbackset>``, add one or more ``<targetedfeedback>`` elements.
* Within each ``<targetedfeedback>`` element, enter your explanation for the incorrect answer in HTML as markup described below.
* Connect the ``<targetedfeedback>`` element with a specific incorrect answer by using the same ``explanation-id`` attribute value for each.
* Use the ``<solution>`` element for the correct answer, with the same ``explanation-id`` attribute value as the correct ``<choice>``.

For example, the XML for the multiple choice problem is:

.. code-block:: xml

   <p>What Apple device competed with the portable CD player?</p>
   <multiplechoiceresponse targeted-feedback="">
    <choicegroup type="MultipleChoice">
      <choice correct="false" explanation-id="feedback1">The iPad</choice>
      <choice correct="false" explanation-id="feedback2">Napster</choice>
      <choice correct="true" explanation-id="correct">The iPod</choice>
      <choice correct="false" explanation-id="feedback3">The vegetable peeler</choice>
    </choicegroup>
   </multiplechoiceresponse>
 
This is followed by XML that defines the targeted feedback:

.. code-block:: xml

   <targetedfeedbackset>
     <targetedfeedback explanation-id="feedback1">
       <div class="detailed-targeted-feedback">
         <p>Targeted Feedback</p>
         <p>The iPad came out later and did not directly compete the portable CD players.</p>
       </div>
     </targetedfeedback>
     <targetedfeedback explanation-id="feedback2">
       <div class="detailed-targeted-feedback">
         <p>Targeted Feedback</p>
         <p>Napster was not an Apple product.</p>
       </div>
     </targetedfeedback>
     <targetedfeedback explanation-id="feedback3">
       <div class="detailed-targeted-feedback">
         <p>Targeted Feedback</p>
         <p>No, not even close.</p>
       </div>
     </targetedfeedback>
    </targetedfeedbackset>

    <solution explanation-id="correct">
     <div class="detailed-solution">
      <p>Yes, the iPod competed with portable CD players.</p>
     </div>
    </solution>


.. _Answer Pools in a Multiple Choice Problem:

=============================================
Answer Pools in a Multiple Choice Problem
=============================================

You can configure a multiple choice problem so that a random subset of choices are shown to each student. For example, you can add 10 possible choices to the problem, and each student views a set of five choices.

The answer pool must have at least one correct answer, and can have more than one. In each set of choices shown to a student, one correct answer is included. For example, you may configure two correct answers in the set of 10. One of the two correct answers is included in each set a student views.

++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Use the Advanced Editor to Configure Answer Pools
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You configure the problem to provide answer pools through XML in :ref:`Advanced Editor`.

Follow these XML guidelines:

* In the ``<choicegroup>`` element, add the ``answer-pool`` attribute, with the numerical value indicating the number of possible answers in the set. For example, ``<choicegroup answer-pool="4">``.

* For each correct answer, to the ``<choice>`` element, add an ``explanation-id`` attribute and value that maps to a solution. For example, ``<choice correct="true" explanation-id="iPod">The iPod</choice>``.

* For each ``<solution>`` element, add an ``explanation-id`` attribute and value that maps back to a correct answer. For example, ``<solution explanation-id="iPod">``.

.. note:: If the choices include only one correct answer, you do not have to use the ``explanation-id`` in either the ``choice`` or ``<solution>`` element. You do still use the ``<solutionset>`` element to wrap the ``<solution>`` element.

For example, for the following multiple choice problem, a student will see four choices, and in each set one of the choices will be one of the two correct ones. The explanation shown for the correct answer is the one with the same explanation ID.

.. code-block:: xml

 <problem>
   <p>What Apple devices let you carry your digital music library in your pocket?</p>
   <multiplechoiceresponse>
    <choicegroup type="MultipleChoice" answer-pool="4">
      <choice correct="false">The iPad</choice>
      <choice correct="false">Napster</choice>
      <choice correct="true" explanation-id="iPod">The iPod</choice>
      <choice correct="false">The vegetable peeler</choice>
      <choice correct="false">The iMac</choice>
      <choice correct="true" explanation-id="iPhone">The iPhone</choice>
    </choicegroup>
   </multiplechoiceresponse>

    <solutionset>
        <solution explanation-id="iPod">
        <div class="detailed-solution">
            <p>Explanation</p>
            <p>Yes, the iPod is Apple's portable digital music player.</p>
        </div>
        </solution>
        <solution explanation-id="iPhone">
        <div class="detailed-solution">
            <p>Explanation</p>
            <p>In addition to being a cell phone, the iPhone can store and play your digital music.</p>
        </div>
        </solution>
    </solutionset>
 </problem>


.. _Numerical Input:

*******************
Numerical Input
*******************

In numerical input problems, students enter numbers or specific and
relatively simple mathematical expressions to answer a question. 

.. image:: ../Images/image292.png
 :alt: Image of a numerical input problem

Note that students' responses don't have to be exact for these problems. You can 
specify a margin of error, or tolerance. You can also specify a correct answer explicitly, or use a Python script. For more information, see the instructions below.

Responses for numerical input problems can include integers, fractions,
and constants such as *pi* and *g*. Responses can also include text
representing common functions, such as square root (sqrt) and log base 2
(log2), as well as trigonometric functions and their inverses, such as
sine (sin) and arcsine (arcsin). For these functions, Studio changes the
text that the student enters into mathematical symbols. The following
example shows the way Studio renders students' text responses in
numerical input problems. 

.. image:: ../Images/Math5.png
 :alt: Image of a numerical input probem rendered by Studio

The following are a few more examples of the way that Studio renders numerical input
text that students enter.

.. image:: ../Images/Math1.png
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math2.png
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math3.png
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math4.png
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math5.png
 :alt: Image of a numerical input probem rendered by Studio

==================
Student Answers
==================

.. _Math Expression Syntax:

+++++++++++++++++++++++
Math Expression Syntax
+++++++++++++++++++++++

In numerical input problems, the **student's input** may be more complicated than a
simple number. Expressions like ``sqrt(3)`` and even ``1+e^(sin(pi/2)+2*i)``
are valid, and evaluate to 1.73 and -0.13 + 2.47i, respectively.

A summary of the syntax follows:

Numbers
~~~~~~~

Accepted number types:

- Integers: '2520'
- Normal floats: '3.14'
- With no integer part: '.98'
- Scientific notation: '1.2e-2' (=0.012)
- More s.n.: '-4.4e+5' = '-4.4e5' (=-440,000)
- Appending SI suffixes: '2.25k' (=2,250). The full list:

  ====== ========== ===============
  Suffix Stands for One of these is
  ====== ========== ===============
  %      percent    0.01 = 1e-2
  k      kilo       1000 = 1e3
  M      mega       1e6
  G      giga       1e9
  T      tera       1e12
  c      centi      0.01 = 1e-2
  m      milli      0.001 = 1e-3
  u      micro      1e-6
  n      nano       1e-9
  p      pico       1e-12
  ====== ========== ===============

The largest possible number handled currently is exactly the largest float
possible (in the Python language). This number is 1.7977e+308. Any expression
containing larger values will not evaluate correctly, so it's best to avoid
this situation.

Default Constants
~~~~~~~~~~~~~~~~~

Simple and commonly used mathematical/scientific constants are included by
default. These include:

- ``i`` and ``j`` as ``sqrt(-1)``
- ``e`` as Euler's number (2.718...)
- ``pi``
- ``k``: the Boltzmann constant (~1.38e-23 in Joules/Kelvin)
- ``c``: the speed of light in m/s (2.998e8)
- ``T``: the positive difference between 0K and 0°C (285.15)
- ``q``: the fundamental charge (~1.602e-19 Coloumbs)

Operators and Functions
~~~~~~~~~~~~~~~~~~~~~~~

The normal operators apply (with normal order of operations):
``+ - * / ^``. Also provided is a special "parallel resistors" operator given
by ``||``. For example, an input of ``1 || 2`` would represent the resistance
of a pair of parallel resistors (of resistance 1 and 2 ohms), evaluating to 2/3
(ohms).

At the time of writing, factorials written in the form '3!' are invalid, but
there is a workaround. Students can specify ``fact(3)`` or ``factorial(3)`` to
access the factorial function.

The default included functions are the following:

- Trig functions: sin, cos, tan, sec, csc, cot
- Their inverses: arcsin, arccos, arctan, arcsec, arccsc, arccot
- Other common functions: sqrt, log10, log2, ln, exp, abs
- Factorial: ``fact(3)`` or ``factorial(3)`` are valid. However, you must take
  care to only input integers. For example, ``fact(1.5)`` would fail.
- Hyperbolic trig functions and their inverses: sinh, cosh, tanh, sech, csch,
  coth, arcsinh, arccosh, arctanh, arcsech, arccsch, arccoth


=================================
Create a Numerical Input Problem 
=================================

You can create numerical problems in the Simple Editor and in the Advanced Editor regardless of the answer to the problem. If the text of your problem doesn't include any italics, bold formatting, or special characters, you can create the problem in the Simple Editor. If the text of your problem contains special formatting or characters, or if your problem contains a Python script, you'll use the Advanced Editor.

For example, the following example problems require the Advanced Editor. 

.. image:: ../Images/NumericalInput_Complex.png
 :alt: Image of a more complex numerical input problem

For more information about including a Python script in your problem, see :ref:`Custom Python Evaluated Input`.


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Create a Numerical Input Problem in the Simple Editor
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Numerical
   Input** on the **Common Problem Types** tab.
   
3. When the new Problem component appears, click **Edit**.
#. In the component editor, replace the sample problem text with your own text.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select the text of the answer, and then click the numerical input button. 

.. image:: ../Images//ProbCompButton_NumInput.png
    :alt: Image of the numerical input button
   
When you do this, an equal sign appears next to the answer.
        
7. (Optional) Specify a margin of error, or tolerance. You can specify a percentage, number, or range.

   * To specify a percentage on either side of the correct answer, add **+-NUMBER%** after the answer. For example, if you want to include a 2% tolerance, add **+-2%**. 

   * To specify a number on either side of the correct answer, add **+-NUMBER** after the answer. For example, if you want to include a tolerance of 5, add **+-5**.

   * To specify a range, use brackets [] or parentheses (). A bracket indicates that range includes the number next to it. A parenthesis indicates that the range does not include the number next to it. For example, if you specify **[5, 8)**, correct answers can be 5, 6, and 7, but not 8. Likewise, if you specify **(5, 8]**, correct answers can be 6, 7, and 8, but not 5.

8. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: ../Images/ProbCompButton_Explanation.png
    :alt: Image of athe explanation button

9. On the **Settings** tab, specify the settings that you want. 
#. Click **Save**.

For the first example problem above, the text in the Problem component is the
following.

::

   >>What base is the decimal numeral system in?<<

   = 10
    
   [explanation]
   The decimal numerial system is base ten.
   [explanation]



+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Create a Numerical Input Problem in the Advanced Editor
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

**Examples**

The following are a few more examples of the way that Studio renders numerical input
text that students enter.

.. image:: ../Images/Math1.gif
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math2.gif
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math3.gif
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math4.gif
 :alt: Image of a numerical input probem rendered by Studio
.. image:: ../Images/Math5.gif
 :alt: Image of a numerical input probem rendered by Studio

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

**Problem Code**:

.. code-block:: xml

  <problem>
    <p><b>Example Problem</b></p>

  <p>What base is the decimal numeral system in?
      <numericalresponse answer="10">
          <formulaequationinput label="What base is the decimal numeral system in?"/>
      </numericalresponse>
  </p>

    <p>What is the value of the standard gravity constant <i>g</i>, measured in m/s<sup>2</sup>? Give your answer to at least two decimal places.
    <numericalresponse answer="9.80665">
      <responseparam type="tolerance" default="0.01" />
      <formulaequationinput label="Give your answer to at least two decimal places"/>
    </numericalresponse>
  </p>

  <!-- Use python script spacing. The following should not be indented! -->
  <script type="loncapa/python">
  computed_response = math.sqrt(math.fsum([math.pow(math.pi,2), math.pow(math.e,2)]))
  </script>

  <p>What is the distance in the plane between the points (pi, 0) and (0, e)? You can type math.
      <numericalresponse answer="$computed_response">
          <responseparam type="tolerance" default="0.0001" />
          <formulaequationinput label="What is the distance in the plane between the points (pi, 0) and (0, e)?"/>
      </numericalresponse>
  </p>
  <solution>
    <div class="detailed-solution">
      <p>Explanation</p>
      <p>The decimal numerical system is base ten.</p>
      <p>The standard gravity constant is defined to be precisely 9.80665 m/s<sup>2</sup>.
      This is 9.80 to two decimal places. Entering 9.8 also works.</p>
      <p>By the distance formula, the distance between two points in the plane is
         the square root of the sum of the squares of the differences of each coordinate.
        Even though an exact numerical value is checked in this case, the
        easiest way to enter this answer is to type
        <code>sqrt(pi^2+e^2)</code> into the editor.
        Other answers like <code>sqrt((pi-0)^2+(0-e)^2)</code> also work.
      </p>
    </div>
  </solution>
  </problem>




.. _Text input:

*******************
Text Input
*******************

In text input problems, students enter text into a response field. The
response can include numbers, letters, and special characters such as
punctuation marks. Because the text that the student enters must match
the instructor's specified answer exactly, including spelling and
punctuation, we recommend that you specify more than one attempt for
text input problems to allow for typographical errors.

.. image:: ../Images/TextInputExample.png
 :alt: Image of a text input probem

==================================
Create a Text Input Problem
==================================

You can create multiple choice problems in the Simple Editor or in the Advanced Editor.

++++++++++++++++++++++++++++++++++++++++++
Simple Editor
++++++++++++++++++++++++++++++++++++++++++

To create a text input problem in the Simple Editor, follow these steps.

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Text Input**
   on the **Common Problem Types** tab.
#. In the new Problem component that appears, click **Edit**.
#. Replace the default text with the text for your problem.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select the text of the answer, and then click the text input button. 
   
   .. image:: ../Images/ProbCompButton_TextInput.png
    :alt: Image of the text input button
   
   When you do this, an equal sign appears next to the answer.
  
   
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: ../Images/ProbCompButton_Explanation.png
    :alt: Image of the explanation button

#. On the **Settings** tab, specify the settings that you want. 
#. Click **Save**.

For the example problem above, the text in the Problem component is the
following.

::

    >>What is the technical term that refers to the fact that, when enough people 
    sleep under a bednet, the disease may altogether disappear?<<
    = herd immunity

    [explanation]
    The correct answer is herd immunity. As more and more people use bednets, 
    the risk of malaria begins to fall for everyone – users and non-users alike. 
    This can fall to such a low probability that malaria is effectively eradicated 
    from the group (even when the group does not have 100% bednet coverage).
    [explanation]

++++++++++++++++++++++++++++++++++++++++++
Advanced Editor
++++++++++++++++++++++++++++++++++++++++++

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

.. code-block:: xml

  <problem>
  <p>
    <em>This problem is adapted from an exercise that first appeared in MITx's 14.73x The Challenges of Global Poverty course, spring 2013.</em>
  </p>
  <p>What is the technical term that refers to the fact that, when enough people sleep under a bednet, the disease may altogether disappear?</p>
  <stringresponse answer=".*herd immunity.*" type="ci regexp">
         <additional_answer>community immunity</additional_answer>
          <additional_answer>population immunity</additional_answer>
          <textline size="20" label="What is the technical term that refers to the fact that, when enough people sleep under a bednet, the disease may altogether disappear?"/>
          <hintgroup>
              <stringhint answer="contact immunity" type="ci" name="contact_immunity_hint" />
              <hintpart on="contact_immunity_hint">
                  <startouttext />
                  In contact immunity, a vaccinated individual passes along his immunity to another person through contact with feces or bodily fluids. The answer to the question above refers to the form of immunity that occurs when so many members of a population are protected, an infectious disease is unlikely to spread to the unprotected population.
                  <endouttext />
              </hintpart >
              <stringhint answer="firewall immunity" type="ci" name="firewall_immunity_hint" />
              <hintpart on="firewall_immunity_hint">
                  <startouttext />
                  Although a firewall provides protection for a population, the term "firewall" is used more in computing and technology than in epidemiology.
                  <endouttext />
              </hintpart >
          </hintgroup>
  </stringresponse>
  <solution>
    <div class="detailed-solution">
      <p>Explanation</p>
      <p>The correct answer is <b>herd immunity</b>. As more and more people use bednets, the risk of malaria begins to fall for everyone – users and non-users alike. This can fall to such a low probability that malaria is effectively eradicated from the group (even when the group does not have 100% bednet coverage).</p>
    </div>
  </solution>
  </problem>




=========================================
Multiple Responses in Text Input Problems
=========================================

You can specify more than one correct response for text input problems. 
For example, instead of requiring students to enter exactly "Dr. Martin Luther 
King, Junior," you can allow answers of "Martin Luther King," "Doctor Martin 
Luther King," and other variations. To do this, you can use the Simple Editor or the Advanced Editor.

++++++++++++++++++++++++++++++++++++++++++
Simple Editor
++++++++++++++++++++++++++++++++++++++++++

To specify additional correct responses in the Simple Editor, include "or=" (without the quotation marks) before each additional correct response.

::

    >>What African-American led the United States civil rights movement during the 1960s?<<
    = Dr. Martin Luther King, Jr.
    or= Dr. Martin Luther King, Junior
    or= Martin Luther King, Jr.
    or= Martin Luther King


++++++++++++++++++++++++++++++++++++++++++
Advanced Editor
++++++++++++++++++++++++++++++++++++++++++

To specify additional correct responses in the Advanced Editor, add an ``<additional_answer>``  for each correct response inside the opening and closing ``<stringresponse>`` tags.

.. code-block:: xml

  <problem>

  <p>What African-American led the United States civil rights movement during the 1960s?</p>
    
  <stringresponse answer="Dr. Martin Luther King, Jr." type="ci" >
    <additional_answer>Dr. Martin Luther King, Junior</additional_answer>
    <additional_answer>Martin Luther King, Jr.</additional_answer>
    <additional_answer>Martin Luther King</additional_answer>
    <textline label="What African-American led the United States civil rights movement during the 1960s?" size="20"/>
  </stringresponse>

  </problem>


=========================================
Case Sensitivity and Text Input Problems
=========================================

By default, text input problems do not require a case sensitive response. You can change this
and require a case sensitive answer.

To make a text input response case sensitive, you must use :ref:`Advanced Editor`.

In the Advanced Editor, you see that the **type** attribute of the **stringresponse** 
element equals **ci**, for *case insensitive*. For example:

::

    <stringresponse answer="Michigan" type="ci">
      <textline size="20"/>
    </stringresponse>

To make the response case sensitive, change the value of the **type** attribute to **cs**.

::

    <stringresponse answer="Michigan" type="cs">
      <textline size="20"/>
    </stringresponse>
    
=============================================
Response Field Length of Text Input Problems
=============================================

By default, the response field for text input problems is 20 characters long. 

You should preview the unit to ensure that the length of the response input field
accommodates the correct answer, and provides extra space for possible incorrect answers.

If the default response field length is not sufficient, you can change it using :ref:`Advanced Editor`.

In the advanced editor, in the XML block for the answer, you see that the **size** attribute of the **textline** element equals **20**:

::

    <stringresponse answer="Democratic Republic of the Congo" type="ci">
      <textline size="20"/>
    </stringresponse>

To change the response field length, change the value of the **size** attribute:

::

    <stringresponse answer="Democratic Republic of the Congo" type="ci">
      <textline size="40"/>
    </stringresponse>

====================================================
Hints and Regular Expressions in Text Input Problems
====================================================

You can provide hints that appear when students enter common incorrect answers in text input problems. You can also set a text input problem to allow a regular expression as an answer. To do this, you'll have to modify the problem's XML in the Advanced Editor. 

The regular expression that the student enters must contain the part of the answer that the instructor specifies. For example, if an instructor has specified  ``<answer=".*example answer.*" type="regexp">``, correct answers include ``example answered``, ``two example answers``, or even ``==example answer==``, but not ``examples`` or ``example anser``.

You can add ``regexp`` to the value of the ``type`` attribute, for example: ``type="ci regexp"`` or ``type="regexp"`` or ``type="regexp cs"``. In this case, any answer or hint are treated as regular expressions.


You can provide hints for common incorrect answers in text input problems. You can also set a text input problem to allow a regular expression as an answer. To do this, you'll have to modify the problem's XML in the Advanced Editor. For more information, see :ref:`Text Input`.

Although you can create text input problems by using the Simple Editor in Studio, you may want to see or change the problem's underlying XML. For example, you can add hints that appear when students enter common incorrect answers, or modify the problem's XML so that students can submit regular expressions as answers. 

The regular expression that the student enters must contain the part of the answer that the instructor specifies. For example, if an instructor has specified  ``<answer=".*example answer.*" type="regexp">``, correct answers include ``example answered``, ``two example answers``, or even ``==example answer==``, but not ``examples`` or ``example anser``.

You can add ``regexp`` to the value of the ``type`` attribute, for example: ``type="ci regexp"`` or ``type="regexp"`` or ``type="regexp cs"``. In this case, any answer or hint will be treated as regular expressions.

**Sample Problem**

.. image:: /Images/TextInputExample.gif
 :alt: Image of a string response problem

**XML Tags**

.. list-table::
   :widths: 20 80

   * - ``<stringresponse>``
     - Indicates that the problem is a text input problem. 
   * - ``<textline>``
     - Child of ``<stringresponse>``. Lists the answer options and contains the ``label`` attribute.
   * - ``<additional_answer>`` (optional)
     - Specifies an additional correct answer for the problem. A problem can contain an unlimited number of additional answers.
   * - ``<hintgroup>`` (optional)
     - Indicates that the instructor has provided hints for certain common incorrect answers.
   * - ``<stringhint />`` (optional)
     - Child of ``<hintgroup>``. Specifies the text of the incorrect answer to provide the hint for. Contains answer, type, name.
   * - ``<hintpart>``
     - Contains the name from ``<stringhint>``. Associates the incorrect answer with the hint text for that incorrect answer.
   * - ``<startouttext />``
     - Indicates the beginning of the text of the hint.
   * - ``<endouttext />``
     - Indicates the end of the text of the hint.

**Sample Problem Code**

.. code-block:: xml

  <problem>
  <p>
    <em>This problem is adapted from an exercise that first appeared in MITx's 14.73x The Challenges of Global Poverty course, spring 2013.</em>
  </p>
  <p>What is the technical term that refers to the fact that, when enough people sleep under a bednet, the disease may altogether disappear?</p>
  <stringresponse answer=".*herd immunity.*" type="ci regexp">
         <additional_answer>community immunity</additional_answer>
          <additional_answer>population immunity</additional_answer>
          <textline size="20" label="What is the technical term that refers to the fact that, when enough people sleep under a bednet, the disease may altogether disappear?"/>
          <hintgroup>
              <stringhint answer="contact immunity" type="ci" name="contact_immunity_hint" />
              <hintpart on="contact_immunity_hint">
                  <startouttext />
                  In contact immunity, a vaccinated individual passes along his immunity to another person through contact with feces or bodily fluids. The answer to the question above refers to the form of immunity that occurs when so many members of a population are protected, an infectious disease is unlikely to spread to the unprotected population.
                  <endouttext />
              </hintpart >
              <stringhint answer="firewall immunity" type="ci" name="firewall_immunity_hint" />
              <hintpart on="firewall_immunity_hint">
                  <startouttext />
                  Although a firewall provides protection for a population, the term "firewall" is used more in computing and technology than in epidemiology.
                  <endouttext />
              </hintpart >
          </hintgroup>
  </stringresponse>
  <solution>
    <div class="detailed-solution">
      <p>Explanation</p>
      <p>The correct answer is <b>herd immunity</b>. As more and more people use bednets, the risk of malaria begins to fall for everyone – users and non-users alike. This can fall to such a low probability that malaria is effectively eradicated from the group (even when the group does not have 100% bednet coverage).</p>
    </div>
  </solution>
  </problem>

**Template**

.. code-block:: xml

  <problem>
      <p>Problem text</p>
      <stringresponse answer="**.Correct answer 1.**" type="ci regexp">
          <additional_answer>Correct answer 2</additional_answer>
          <additional_answer>Correct answer 3</additional_answer>
          <textline size="20" label="label text"/>
          <hintgroup>
              <stringhint answer="Incorrect answer A" type="ci" name="hintA" />
                <hintpart on="hintA">
                    <startouttext />Text of hint for incorrect answer A<endouttext />
                </hintpart >
              <stringhint answer="Incorrect answer B" type="ci" name="hintB" />
                <hintpart on="hintB">
                    <startouttext />Text of hint for incorrect answer B<endouttext />
                </hintpart >
              <stringhint answer="Incorrect answer C" type="ci" name="hintC" />
                <hintpart on="hintC">
                    <startouttext />Text of hint for incorrect answer C<endouttext />
                </hintpart >
          </hintgroup>
      </stringresponse>
      <solution>
      <div class="detailed-solution">
      <p>Explanation or Solution Header</p>
      <p>Explanation or solution text</p>
      </div>
    </solution>
  </problem>

You can provide hints for common incorrect answers in text input problems. You can also set a text input problem to allow a regular expression as an answer. To do this, you'll have to modify the problem's XML in the Advanced Editor. For more information, see :ref:`Text Input`.
