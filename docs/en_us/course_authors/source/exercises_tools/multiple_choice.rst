.. _Multiple Choice:

########################
Multiple Choice Problem
########################

In multiple choice problems, students select one option from a list of answer options. Unlike with dropdown problems, whose answer choices don't appear until the student clicks the drop-down arrow, answer choices for multiple choice problems are always visible directly below the question.

.. image:: /Images/MultipleChoiceExample.png
 :alt: Image of a multiple choice problem

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