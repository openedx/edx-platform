.. _Problem Written in LaTeX:

############################
Problem Written in LaTeX
############################

.. warning:: This problem type is still a prototype and may not be supported in the future. By default, the ability to create these problems is not enabled in Studio. You must change the advanced settings in your course before you can create problems with LaTeX. Use this problem type with caution.

If you have an problem that is already written in LaTeX, you can use this problem type to easily convert your code into XML. After you paste your code into the LaTeX editor, you'll only need to make a few minor adjustments. 

.. note:: If you want to use LaTeX to typeset mathematical expressions
          in problems that you haven't yet written, use any of the other problem
          templates together with `MathJax <http://www.mathjax.org>`_. For more
          information about how to create mathematical expressions in Studio using
          MathJax, see *A Brief Introduction to MathJax in Studio*.

.. image:: /Images/ProblemWrittenInLaTeX.png
 :alt: Image of a problem written in LaTeX

************************************
Create a Problem Written in LaTeX
************************************

To create a problem written in LaTeX:

#. Enable the policy key in your course.

   #. In Studio, click **Settings**, and then click **Advanced Settings**.
   #. In the field for the **Enable LaTeX Compiler** policy key, change
      **false** to **true**.
   #. At the bottom of the page, click **Save Changes**.
   
#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Problem Written in LaTeX**.
#. In the component editor that appears, click **Edit**.
#. In the lower left corner of the component editor, click **Launch
   LaTeX Source Compiler**.
#. Replace the example code with your own code. You can also upload a Latex file into the editor from your computer by clicking **Upload** in the bottom right corner.
#. In the lower left corner of the LaTeX source compiler, click **Save &
   Compile to edX XML**.