.. _Protein Builder:

############################
Protex Protein Builder Tool
############################

The Protex protein builder asks students to create specified protein shapes by stringing together amino acids. In the example below, the goal protein shape is a simple line. 


.. image:: /Images/ProteinBuilder.png
  :alt: Image of the protein builder

.. _Create the Protein Builder:

********************************
Create the Protein Builder Tool
********************************

To create the protein builder:

#. Under **Add New Component**, click **Problem**, and then click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. In the component editor, paste the Problem component code from below.
#. Make any changes that you want, and then click **Save**.

.. _Protein Builder Code:

*************************
Protein Builder Tool Code
*************************

.. code-block:: xml

  <problem>
      <p>The protein builder allows you string together the building blocks of proteins, amino acids, and see how that string will form into a structure. You are presented with a goal protein shape, and your task is to try to re-create it. In the example below, the shape that you are asked to form is a simple line.</p> 
     <p>Be sure to click "Fold" to fold your protein before you click "Check".</p>

  <script type="loncapa/python">

  def protex_grader(expect,ans):
    import json
    ans=json.loads(ans)
    if "ERROR" in ans["protex_answer"]:
      raise ValueError("Protex did not understand your answer. Try folding the protein.")
    return ans["protex_answer"]=="CORRECT"

  </script>
 
    <text>
      <customresponse cfn="protex_grader">
        <designprotein2dinput width="855" height="500" target_shape="W;W;W;W;W;W;W"/>
      </customresponse>
    </text>
    <solution>
      <p>
        Many protein sequences, such as the following example, fold to a straight line.You can play around with the protein builder if you're curious.
      </p>
      <ul>
        <li>
            Stick: RRRRRRR
        </li>
      </ul>
    </solution>
  </problem>

In this code:
 
* **width** and **height** specify the dimensions of the application, in pixels.
* **target_shape** lists the amino acids that, combined in the order specified, create the shape you've asked students to create. The list can only include the following letters, which correspond to the one-letter code for each amino acid. (This list appears in the upper-left corner of the protein builder.)

  .. list-table::
     :widths: 15 15 15 15
     :header-rows: 0

     * - A
       - R
       - N
       - D
     * - C
       - Q
       - E
       - G
     * - H
       - I
       - L
       - K
     * - M
       - F
       - P
       - S
     * - T
       - W
       - Y
       - V
