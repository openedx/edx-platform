.. _Checkbox:

##################
Checkbox Problem
##################

In checkbox problems, the student selects one or more options from a list of possible answers. The student must select all the options that apply to answer the problem correctly. Each checkbox problem must have at least one correct answer.

.. image:: /Images/CheckboxExample.png
 :alt: Image of a checkbox problem

****************************
Create a Checkbox Problem
****************************

You can create checkbox problems in the Simple Editor or in the Advanced Editor.

.. note:: All problems must include labels for accessibility. The label generally includes the text of the main question in your problem. To add a label for a common problem, surround the text of the label with angle brackets pointed toward the text (>>label text<<).

==================
Simple Editor
==================

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Checkboxes** on the **Common Problem Types** tab.
#. In the Problem component that appears, click **Edit**.
#. In the component editor, replace the default text with the text of your 
   problem. Enter each answer option on its own line.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select all the answer options, and then click the checkbox button. 

   .. image:: /Images/ProbComponent_CheckboxIcon.png
    :alt: Image of the checkbox button
   
   When you do this, brackets appear next to each answer choice.

#. Add an **x** between the brackets for the correct answer or answers.
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: /Images/ProbCompButton_Explanation.png
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

==================
Advanced Editor
==================

To create this problem in the Advanced Editor, click the **Advanced** tab in the Problem component editor, and then replace the existing code with the following code.

.. code-block:: xml

  <problem>
    <p>Learning about the benefits of preventative healthcare can be particularly difficult. Check all of the reasons below why this may be the case.</p>

  <choiceresponse>
    <checkboxgroup direction="vertical" label="Check all of the reasons below why this may be the case">
      <choice correct="true"><text>A large amount of time passes between undertaking a preventative measure and seeing the result.</text></choice>
      <choice correct="false"><text>Non-immunized people will always fall sick.</text></choice>
      <choice correct="true"><text>If others are immunized, fewer people will fall sick regardless of a particular individual's choice to get immunized or not.</text></choice>
      <choice correct="true"><text>Trust in healthcare professionals and government officials is fragile.</text></choice>
    </checkboxgroup>
  </choiceresponse>

   <solution>
   <div class="detailed-solution">
   <p>Explanation</p>
   <p>People who are not immunized against a disease may still not fall sick from the disease. If someone is trying to learn whether or not preventative measures against the disease have any impact, he or she may see these people and conclude, since they have remained healthy despite not being immunized, that immunizations have no effect. Consequently, he or she would tend to believe that immunization (or other preventative measures) have fewer benefits than they actually do.</p>
   </div>
   </solution>
  </problem>

.. _Checkbox Problem XML:

****************************
Checkbox Problem XML 
****************************

============
Template
============

.. code-block:: xml

  <problem>
    <p>Question text</p>

  <choiceresponse>

  <checkboxgroup direction="vertical" label="label text">
  <choice correct="false"><text>Answer option 1 (incorrect)</text></choice>
  <choice correct="true"><text>Answer option 2 (correct)</text></choice>
  </checkboxgroup>
  </choiceresponse>

   <solution>
   <div class="detailed-solution">
   <p>Solution or Explanation Heading</p>
   <p>Solution or explanation text</p>
   </div>
   </solution>

  </problem>

======
Tags
======

* ``<choiceresponse>`` (required): Specifies that the problem contains options for students to choose from.
* ``<checkboxgroup>`` (required): Specifies that the problem is a checkbox problem.
* ``<choice>`` (required): Designates an answer option.

**Tag:** ``<choiceresponse>``

Specifies that the problem contains options for students to choose from.

  Attributes

  (none)

  Children

  * ``<checkboxgroup>``

**Tag:** ``<checkboxgroup>``

Specifies that the problem is a checkbox problem.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - direction (optional)
       - Specifies the orientation of the list of answers. The default is vertical.
     * - label (required)
       - Specifies the name of the response field.

  Children

  * ``<choice>`` 

**Tag:** ``<choice>``

Designates an answer option.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - true (at least one required)
       - Indicates a correct answer. For checkbox problems, one or more ``<choice>`` tags can contain a correct answer.
     * - false (at least one required)
       - Indicates an incorrect answer.

  Children
  
  (none)
