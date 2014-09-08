.. _Multiple Choice:

########################
Multiple Choice Problem
########################

In multiple choice problems, students select one option from a list of answer options. Unlike with dropdown problems, whose answer choices don't appear until the student clicks the drop-down arrow, answer choices for multiple choice problems are always visible directly below the question.

.. image:: /Images/MultipleChoiceExample.png
 :alt: Image of a multiple choice problem

Multiple choice problems also have several advanced options, such as presenting a random set of choices to each student. For more information about these options, see :ref:`Multiple Choice Advanced Options`.

****************************************
Create a Multiple Choice Problem
****************************************

You can create multiple choice problems in the Simple Editor or in the Advanced Editor.

.. note:: All problems must include labels for accessibility. The label generally includes the text of the main question in your problem. To add a label for a common problem, surround the text of the label with angle brackets pointed toward the text (>>label text<<).

================
Simple Editor
================

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Multiple
   Choice** on the **Common Problem Types** tab.
#. When the new Problem component appears, click **Edit**.
#. In the component editor, replace the sample problem text with the text of your 
   problem. Enter each answer option on its own line.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select all the answer options, and then click the multiple choice button. 
   
   .. image:: /Images/ProbCompButton_MultChoice.png
    :alt: Image of the multiple choice button
   
   When you do this, the component editor adds a pair of parentheses next to each 
   possible answer.
   
#. Add an "x" between the parentheses next to the correct answer.
   
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: /Images/ProbCompButton_Explanation.png
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

================
Advanced Editor
================

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

.. _Multiple Choice Advanced Options:

*********************************************
Advanced Options for Multiple Choice Problems
*********************************************

Multiple choice problems have several advanced options. You can change the order of answers in the problem, include explanations that appear when a student selects a specific incorrect answer, or present a random set of choices to each student. For more information, see the following:


* :ref:`Shuffle Answers in a Multiple Choice Problem`
* :ref:`Targeted Feedback in a Multiple Choice Problem`
* :ref:`Answer Pools in a Multiple Choice Problem`

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


Use the Simple Editor to Shuffle Answers
*********************************************

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

Use the Advanced Editor to Shuffle Answers
*********************************************

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

You can configure a multiple choice problem so that explanations for incorrect answers are automatically shown to students. You can use these explanations to guide students towards the right answer. Therefore, targeted feedback is most useful for multiple choice problems for which students are allowed multiple attempts.


Use the Advanced Editor to Configure Targeted Feedback
********************************************************

You configure the problem to provide targeted feedback through XML in :ref:`Advanced Editor`.

Follow these XML guidelines:

* Add a ``targeted-feedback`` attribute to the ``<multiplechoiceresponse>`` element, with no value: ``<multiplechoiceresponse targeted-feedback="">``
* Add a ``<targetedfeedbackset>`` element before the ``<solution>`` element.
* Within ``<targetedfeedbackset>``, add one or more ``<targetedfeedback>`` elements.
* Within each ``<targetedfeedback>`` element, enter your explanation for the incorrect answer in HTML as markup described below.
* Connect the ``<targetedfeedback>`` element with a specific incorrect answer by using the same ``explanation-id`` attribute value for each.
* Use the ``<solution>`` element for the correct answer, with the same ``explanation-id`` attribute value as the correct ``<choice>`` element.

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
         <p>The iPad came out later and did not directly compete with portable CD players.</p>
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
         <p>Vegetable peelers don't play music.</p>
       </div>
     </targetedfeedback>
    </targetedfeedbackset>

    <solution explanation-id="correct">
     <div class="detailed-solution">
      <p>The iPod directly competed with portable CD players.</p>
     </div>
    </solution>


.. _Answer Pools in a Multiple Choice Problem:

=============================================
Answer Pools in a Multiple Choice Problem
=============================================

You can configure a multiple choice problem so that a random subset of choices are shown to each student. For example, you can add 10 possible choices to the problem, and each student views a set of five choices.

The answer pool must have at least one correct answer, and can have more than one. In each set of choices shown to a student, one correct answer is included. For example, you may configure two correct answers in the set of 10. One of the two correct answers is included in each set a student views.

Use the Advanced Editor to Configure Answer Pools
**************************************************

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


.. _Multiple Choice Problem XML:

******************************
Multiple Choice Problem XML 
******************************

================
Template
================

.. code-block:: xml

  <problem>
  <p>Question text</p>
  <multiplechoiceresponse>
    <choicegroup type="MultipleChoice" label="label text">
      <choice correct="false" name="a">Incorrect choice</choice>
      <choice correct="true" name="b">Correct choice</choice>
    </choicegroup>
  </multiplechoiceresponse>

  <solution>
    <div class="detailed-solution">
    <p>Explanation or solution header</p>
    <p>Explanation or solution text</p>
    </div>
  </solution>
  </problem>

================
Tags
================

* ``<multiplechoiceresponse>`` (required): Indicates that the problem is a multiple choice problem.
* ``<choicegroup>`` (required): Indicates the beginning of the list of options. 
* ``<choice>`` (required): Lists an answer option.

**Tag:** ``<multiplechoiceresponse>``

Indicates that the problem is a multiple choice problem.

  Attributes

  (none)

  Children

  * ``<choicegroup>``
  * All standard HTML tags (can be used to format text)

**Tag:** ``<choicegroup>``

Indicates the beginning of the list of options.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - label (required)
       - Specifies the name of the response field.
     * - type (required)
       - Must be set to "MultipleChoice".

  Children

  * ``<choice>`` 

**Tag:** ``<choice>``

Lists an answer option. 

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - correct (at least one required)
       - Indicates a correct or incorrect answer. When the attribute is set to "true", the choice is a correct answer. When the attribute is set to "false", the choice is an incorrect answer. Only one choice can be a correct answer.
     * - name
       - A unique name that the back end uses to refer to the choice.

  Children
  
  (none)