.. _Chemical Equation:

################################
Chemical Equation Problem
################################

The chemical equation problem type allows the student to enter text that represents a chemical equation into a text box. The system converts that text into a chemical equation below the text box. The grader evaluates the student's response by using a Python script that you create and embed in the problem.

.. image:: /Images/ChemicalEquationExample.png
 :alt: Image of a chemical equation response problem

************************************
Create the Chemical Equation Problem
************************************

Chemical equation problems use MathJax to create formulas. For more information about using MathJax in Studio, see :ref:`MathJax in Studio`.

To create the above chemical equation problem:

#. In the unit where you want to create the problem, click **Problem** under **Add New Component**, and then click the **Advanced** tab.
#. Click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. In the component editor, paste the code from below.
#. Click **Save**.

==========================================
Sample Chemical Equation Problem Code
==========================================

.. code-block:: xml

  <problem>
    <startouttext/>
    <p>Some problems may ask for a particular chemical equation. Practice by writing out the following reaction in the box below.</p>
    
  \( \text{H}_2\text{SO}_4 \longrightarrow \text { H}^+ + \text{ HSO}_4^-\)

    <customresponse>
      <chemicalequationinput size="50" label="Enter the chemical equation"/>
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

.. _Chemical Equation Problem XML:

************************************
Chemical Equation Problem XML
************************************

============
Template
============

.. code-block:: xml

  <problem>
    <startouttext/>
    <p>Problem text</p>

    <customresponse>
      <chemicalequationinput size="NUMBER" label="LABEL TEXT"/>
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

======
Tags
======

* ``<customresponse>``: Indicates that this problem has a custom response. 
* ``<chemicalequationinput>``: Specifies that the answer to this problem is a chemical equation. 
* ``<answer type=loncapa/python>``: Contains the Python script that grades the problem.

**Tag:** ``<customresponse>``

Indicates that this problem has a custom response. The ``<customresponse>`` tags must surround the ``<chemicalequation>`` tags.

  Attributes

  (none)

  Children

  * ``<chemicalequationinput>``
  * ``<answer>``

**Tag:** ``<chemicalequationinput>``

Indicates that the answer to this problem is a chemical equation and creates a response field where the student enters an answer.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - size 
       - Specifies the size of the response field, in characters.
     * - label (required)
       - Contains the text of the principal question in the problem.

  Children
  
  (none)

**Tag:** ``<answer>``

Contains the Python script that grades the problem.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - type (required) 
       - Must be "loncapa/python".

  Children
  
  (none)
     
