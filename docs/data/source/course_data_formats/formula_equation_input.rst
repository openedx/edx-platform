Formula Equation Input
######################

  Tag: ``<formulaequationinput />``

The formula equation input is a math input type used with Numerical and Formula
responses only. It is not to be used with Symoblic Response. It is comparable
to a ``<textline math="1"/>`` but with a different means to display the math.
It lets the platform validate the student's input as she types.

This is achieved by periodically sending the typed expression and requesting
its preview from the LMS. It parses the expression (using the same parser as
the parser it uses to eventually evaluate the response for grading), and sends
back an OK'd copy.

The basic appearance is that of a textbox with a preview box below it. The
student types in math (see note below for syntax), and a typeset preview
appears below it. Even complicated math expressions may be entered in.

For more information about the syntax, look in the course author's
documentation, under Appendix E, the section about Numerical Responses.

Format
******

The XML is rather simple, it is a ``<formulaequationinput />`` tag with an
optional ``size`` attribute, which defines the size (i.e. the width) of the
input box displayed to students for typing their math expression. Unlike
``<textline />``, there is no ``math`` attribute and adding such will have no
effect.

To see an example of the input type in context:

.. code-block:: xml

  <problem>
    <p>What base is the decimal numeral system in?</p>
    <numericalresponse answer="10">
      <formulaequationinput />
    </numericalresponse>

    <p>Write an expression for the product of R_1, R_2, and the inverse of R_3.</p>
    <formularesponse type="ci" samples="R_1,R_2,R_3@1,2,3:3,4,5#10" answer="R_1*R_2/R_3">
      <responseparam type="tolerance" default="0.00001"/> 
      <formulaequationinput size="40" />
    </formularesponse>
  </problem>
