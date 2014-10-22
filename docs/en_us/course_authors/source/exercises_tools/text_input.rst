.. _Text Input:

########################
Text Input Problem
########################



In text input problems, students enter text into a response field. The response can include numbers, letters, and special characters such as punctuation marks. Because the text that the student enters must match the instructor's specified answer exactly, including spelling and punctuation, we recommend that you specify more than one attempt for text input problems to allow for typographical errors.

.. image:: /Images/TextInputExample.png
 :alt: Image of a text input probem

****************************
Create a Text Input Problem
****************************

You can create text input problems in the Simple Editor or in the Advanced Editor.

.. note:: All problems must include labels for accessibility. The label generally includes the text of the main question in your problem. To add a label for a common problem, surround the text of the label with angle brackets pointed toward the text (>>label text<<).

==============
Simple Editor
==============

To create a text input problem in the Simple Editor, follow these steps.

#. Under **Add New Component**, click **Problem**.
#. In the **Select Problem Component Type** screen, click **Text Input**
   on the **Common Problem Types** tab.
#. In the new Problem component that appears, click **Edit**.
#. Replace the default text with the text for your problem.
#. Determine the text of the problem to use as a label, and then surround that text with two sets of angle brackets (>><<).
#. Select the text of the answer, and then click the text input button. 
   
   .. image:: /Images/ProbCompButton_TextInput.png
    :alt: Image of the text input button
   
   When you do this, an equal sign appears next to the answer.
  
   
#. In the component editor, select the text of the explanation, and then click the 
   explanation button to add explanation tags around the text.

   .. image:: /Images/ProbCompButton_Explanation.png
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

=====================
Advanced Editor
=====================

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




******************************************
Multiple Responses in Text Input Problems
******************************************

You can specify more than one correct response for text input problems. 
For example, instead of requiring students to enter exactly "Dr. Martin Luther 
King, Junior," you can allow answers of "Martin Luther King," "Doctor Martin 
Luther King," and other variations. To do this, you can use the Simple Editor or the Advanced Editor.

==============
Simple Editor
==============

To specify additional correct responses in the Simple Editor, include "or=" (without the quotation marks) before each additional correct response.

::

    >>What African-American led the United States civil rights movement during the 1960s?<<
    = Dr. Martin Luther King, Jr.
    or= Dr. Martin Luther King, Junior
    or= Martin Luther King, Jr.
    or= Martin Luther King

=====================
Advanced Editor
=====================

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


******************************************
Case Sensitivity and Text Input Problems
******************************************

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

*************************************************
Response Field Length of Text Input Problems
*************************************************

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

********************************************************
Hints and Regular Expressions in Text Input Problems
********************************************************

You can provide hints that appear when students enter common incorrect answers in text input problems. You can also set a text input problem to allow a regular expression as an answer. To do this, you'll have to modify the problem's XML in the Advanced Editor. 

The regular expression that the student enters must contain the part of the answer that the instructor specifies. For example, if an instructor has specified  ``<answer=".*example answer.*" type="regexp">``, correct answers include ``example answered``, ``two example answers``, or even ``==example answer==``, but not ``examples`` or ``example anser``.

You can add ``regexp`` to the value of the ``type`` attribute, for example: ``type="ci regexp"`` or ``type="regexp"`` or ``type="regexp cs"``. In this case, any answer or hint are treated as regular expressions.

.. _Text Input Problem XML:

***********************
Text Input Problem XML
***********************

==============
Template
==============

.. code-block:: xml

  <problem>
      <p>Problem text</p>
      <stringresponse answer="Correct answer 1" type="ci regexp">
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

=======
Tags
=======

* ``<stringresponse>``: Indicates that the problem is a text input problem. 
* ``<textline>``: Child of ``<stringresponse>``. Creates a response field in the LMS where the student enters a response.
* ``<additional_answer>`` (optional): Specifies an additional correct answer for the problem. A problem can contain an unlimited number of additional answers.
* ``<hintgroup>`` (optional): Indicates that the instructor has provided hints for certain common incorrect answers.
* ``<stringhint />`` (optional): Child of ``<hintgroup>``. Specifies the text of the incorrect answer to provide the hint for. Contains answer, type, name.
* ``<hintpart>``: Contains the name from ``<stringhint>``. Associates the incorrect answer with the hint text for that incorrect answer.
* ``<startouttext />``: Indicates the beginning of the text of the hint.
* ``<endouttext />``: Indicates the end of the text of the hint.

**Tag:** ``<stringresponse>``

Indicates that the problem is a text input problem.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - answer (required)
       - Specifies the correct answer. To designate the answer as a regular expression, add "regexp" to the **type** attribute. If you do not add "regexp" to the **type** attribute, the student's answer must match the value in this attribute exactly.
     * - type (optional)
       - Can specify whether the problem is case sensitive and allows regular expressions. If the ``<stringresponse>`` tag includes ``type="ci"``, the problem is not case sensitive. If the tag includes ``type="cs"``, the problem is case sensitive. If the tag includes ``type="regexp"``, the problem allows regular expressions. A **type** attribute in a ``<stringresponse>`` tag can also combine these values. For example, ``<stringresponse type="regexp cs">`` specifies that the prolem allows regular expressions and is case sensitive.

  Children

  * ``<textline />`` (required)
  * ``<additional_answer>`` (optional)
  * ``<hintgroup>`` (optional)
    
**Tag:** ``<textline />``
 
Creates a response field in the LMS where the student enters a response.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - label (required)
       - Contains the text of the problem.
     * - size (optional)
       - Specifies the size, in characters, of the response field in the LMS.
     * - hidden (optional)
       - If set to "true", students cannot see the response field.
     * - correct_answer (optional)
       - Lists the correct answer to the problem.

  Children
  
  (none)

**Tag:** ``<additional_answer>``

Specifies an additional correct answer for the problem. A problem can contain an unlimited number of additional answers.

  Attributes

  (none)

  Children

  (none)

**Tag:** ``<hintgroup>``

Indicates that the instructor has provided hints for certain common incorrect answers.

  Attributes

  (none)

  Children
  
  * ``<stringhint>`` (required)

**Tag:** ``<stringhint>``

Specifies a common incorrect answer to the problem.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - answer (required)
       - The text of the incorrect answer.
     * - name (required)
       - The name of the hint that you want to provide.
     * - type
       - Specifies whether the text of the specified incorrect answer is case sensitive. Can be set to "cs" (case sensitive) or "ci" (case insensitive).

  Children

  * ``<hintpart>`` (required)

**Tag:** ``<hintpart>``

Associates a common incorrect answer with the hint for that incorrect answer.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - on
       - The name of the hint. This must be the same as the **name** attribute of the ``<stringhint>`` tag. (The ``<stringhint>`` tag provides the name of the hint and the incorrect answer to associate with the hint. The ``<hintpart>`` tag contains the name of the hint and the text of the hint.)

  Children

  * ``<startouttext />`` (required)
  * ``<endouttext />`` (required)

**Tags:** ``<startouttext />`` and ``<endouttext>``

Surround the text of the hint.

  Attributes
  
  (none)

  Children
  
  (none)

