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

