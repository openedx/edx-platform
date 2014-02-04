.. _Additional Tools:


#############################
Additional Tools
#############################

*************************
Additional Tools Overview
*************************

Individual course teams frequently create tools and problem types that don't have templates in Studio. We want to make these tools available to all our course teams. We provide you with all the files and code that you need to create these problems in Studio.

Below, you'll find the information you need to create the following tools.

* :ref:`Multiple Choice and Numerical Input`
* :ref:`Protein Builder`

.. _Multiple Choice and Numerical Input:

*******************************************
Multiple Choice and Numerical Input Problem
*******************************************

A multiple choice and numerical input problem combines a multiple choice problem with a numerical input problem. Students not only select a response from options that you provide, but also provide more specific information, if necessary.

.. image:: /Images/MultipleChoice_NumericalInput.gif
  :alt: Image of a multiple choice and numerical input problem

.. note:: Currently, students can only enter numerals in the text field. Students cannot enter words or mathematical expressions.

.. _Create an MCNA Problem:

====================================================
Create a Multiple Choice and Numerical Input Problem
====================================================

To create a multiple choice and numerical input problem:

#. In the unit where you want to create the problem, click **Problem** under **Add New Component**, and then click the **Advanced** tab.
#. Click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. In the component editor, paste the code from below.
#. Replace the example problem and response options with your own text.
#. Click **Save**.

.. _MCNA Problem Code:

===================================================
Multiple Choice and Numerical Input Problem Code
===================================================

::

  <problem>
  The numerical value of pi, rounded to two decimal points, is 3.24.
  <choicetextresponse>
  <radiotextgroup>
  <choice correct="false">True.</choice>
  <choice correct="true">False. The correct value is <numtolerance_input answer="3.14"/>.</choice>
  </radiotextgroup>
  </choicetextresponse>
  </problem>

.. _Protein Builder:

************************
Protein Builder
************************

The protein builder asks students to create specified protein shapes by stringing together amino acids. In the example below, the goal protein shape is a simple line. 


.. image:: /Images/ProteinBuilder.gif
  :alt: Image of the protein builder

.. _Create the Protein Builder:

==========================
Create the Protein Builder
==========================

To create the protein builder:

#. Upload all of the files listed above to the *Files & Uploads* page in your course.
#. Under the HTML component, click **Problem** under **Add New Component**, and then click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. In the component editor, paste the Problem component code from below.
#. Make any changes that you want, and then click **Save**.

.. _Protein Builder Code:

=====================
Protein Builder Code
=====================

::

  <problem>
      <p>The protein builder allows you string together the building blocks of proteins, amino acids, and see how that string will form into a structure. You are presented with a goal protein shape, and your task is to try to re-create it. In the example below, the shape that you are asked to form is a simple line.</p> 

      <script type="loncapa/python">

  def two_d_grader(expect,ans):
    import json
    ans=json.loads(ans)
    if "ERROR" in ans["protex_answer"]:
      raise ValueError("Protex did not understand your answer... try folding the protein")
    return ans["protex_answer"]=="CORRECT"


  </script>
    <text>
      <customresponse cfn="two_d_grader">
        <designprotein2dinput width="855" height="500" target_shape="W;W;W;W;W;W;W"/>
      </customresponse>
    </text>
    <p>Be sure to click "Fold" to fold your protein before you click "Check".</p>
    <solution>
      <p>
              There are many protein sequences that will fold to the shape we asked you
              about. Here is a sample sequence that will work. You can play around with
              it if you are curious.
          </p>
      <ul>
        <li>
                  Stick: RRRRRRR
              </li>
      </ul>
    </solution>
  </problem>
