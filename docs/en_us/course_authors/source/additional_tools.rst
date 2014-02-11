.. _Additional Tools:


#############################
Additional Tools
#############################

*************************
Additional Tools Overview
*************************

Individual course teams frequently create tools and problem types that don't have templates in Studio. We want to make these tools available to all our course teams. We provide you with all the files and code that you need to create these problems in Studio.

Below, you'll find the information you need to create the following tools.

* :ref:`Gene Editor`
* :ref:`Interactive Periodic Table`
* :ref:`Molecule Editor`
* :ref:`Multiple Choice and Numerical Input`
* :ref:`Protein Builder`

.. _Gene Editor:

**************************
Genex Gene Editor
**************************

.. warning:: Description of gene editor--I'm not sure what this tool does, exactly. Help?

.. image:: /Images/GeneEditor.gif
  :alt: Image of the interactive periodic table

.. _Create the Gene Editor:

==========================
Create the Gene Editor
==========================

#. In the unit where you want to create the problem, click **Problem** under **Add New Component**, and then click the **Advanced** tab.
#. Click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. In the component editor, paste the code from below.
#. Click **Save**.

=====================
Gene Editor Code
=====================

.. warning:: Jean-Michel, can you provide problem text for this?

::

<problem>
<script type="loncapa/python">
def genex_grader(expect,ans):
    if ans=="CORRECT": return True
    import json
    ans=json.loads(ans)
    return ans["genex_answer"]=="CORRECT"
</script>
<customresponse cfn="genex_grader">
<editageneinput width="818" height="1000" dna_sequence="TAAGGCTATAACCGAGATTGATGCCTTGTGCGATAAGGTGTGTCCCCCCCCAAAGTGTCGGATGTCGAGTGCGCGTGCAAAAAAAAACAAAGGCGAGGACCTTAAGAAGGTGTGAGGGGGCGCTCGAT" genex_dna_sequence="TAAGGCTATAACCGAGATTGATGCCTTGTGCGATAAGGTGTGTCCCCCCCCAAAGTGTCGGATGTCGAGTGCGCGTGCAAAAAAAAACAAAGGCGAGGACCTTAAGAAGGTGTGAGGGGGCGCTCGAT" genex_problem_number="2"/>
</customresponse>
</problem>

.. note::

In this code:

* **width** and **height** specify the dimensions of the application, in pixels.
* **genex_dna_sequence** is the default DNA sequence that appears when the problem opens.
* **dna_sequence** contains the application's state and the student's answer. This value must be the same as **genex_dna_sequence**. 
* **genex_problem_number** determines what the user has to find to answer the problem correctly. It is hard-coded in the Java GWT code that is used to produce the JS. Its value can range from 1 to 5 and corresponds to the 5 'Edit a Gene' problems encountered in 7.00x.

.. warning:: Jean-Michel: I'm not sure what to say about **genex_problem_number, since this info is just for 7.00x. Would something like this work?

  **genex_problem_number** specifies the number of the problem. This number is based on the five gene editor problems in the MITx 7.00x course--for example, if you want this problem to look like the second gene editor problem in the 7.00x course, you would set the **genex_problem_number** value to 2. The number must be 1, 2, 3, 4, or 5.

  (This seems a little odd--do all courses have to use the same five gene editor problems?)


.. _Interactive Periodic Table:

**************************
Interactive Periodic Table
**************************

You can create an interactive periodic table of the elements to help your students learn about various elements' properties. In the table below, detailed information about each element appears as the student moves the mouse over the element.

.. image:: /Images/Periodic_Table.gif
  :alt: Image of the interactive periodic table

.. _Create the Periodic Table:

==========================
Create the Periodic Table
==========================

To create a periodic table, you need the following files:

* Periodic-Table.js
* Periodic-Table.css
* Periodic-Table-Colors.css
* PeriodicTableHTML.txt

To download all of these files in a .zip archive, click http://files.edx.org/PeriodicTableFiles.zip. 

To create the periodic table, you need an HTML component.

#. Upload all of the files listed above *except PeriodicTable.txt* to the **Files & Uploads** page in your course.
#. In the unit where you want to create the problem, click **HTML** under **Add New Component**, and then click **HTML**.
#. In the component that appears, click **Edit**.
#. In the component editor, switch to the **HTML** tab.
#. Open the PeriodicTable.txt file in any text editor.
#. Copy all of the text in the PeriodicTable.txt file, and paste it into the HTML component editor. (Note that the PeriodicTableHTML.txt file contains over 6000 lines of code. Paste all of this code into the component editor.)
#. Make any changes that you want, and then click **Save**.

.. _Molecule Editor:

************************
Molecule Editor
************************

.. warning:: Jean-Michel: I started creating documentation for this a couple of weeks ago, based on the molecule editor in the demo course. In addition to the problem XML that you provided, that problem included some HTML text as well. Can you look over it and let me know if you think it's OK to keep that in? (To be honest, the two collapsible sections in the HTML component look kind of ugly in the LMS, so I'm happy to hear any suggestions for them.)

Students can use the molecule editor to learn how to create molecules. The molecule editor allows students to draw molecules that follow the rules for covalent bond formation and formal charge, but are chemically impossible. The molecule editor warns students if they try to submit a structure that is not possible.

The molecule editor incorporates two tools: the JSME molecule editor created by Peter Erl and Bruno Bienfait, and JSmol, a JavaScript-based molecular viewer from Jmol. (You don't need to download either of these tools--Studio uses them automatically.) For more information about the JSME molecule editor, see `JSME Molecule Editor <http://peter-ertl.com/jsme/index.html>`_. For more information about JSmol, see `JSmol <http://sourceforge.net/projects/jsmol/>`_.

.. image:: /Images/Molecule_Editor.gif
  :alt: Image of the molecule editor

.. _Create the Molecule Editor:

==========================
Create the Molecule Editor
==========================

To create a molecule editor, you need the following files:

* MoleculeAnswer.png
* MoleculeEditor_HTML.png
* Molecules_Dopamine.mol

To download all of these files in a .zip archive, go to http://files.edx.org/MoleculeEditorFiles.zip.

.. note:: The molecule that appears when the tool starts is a dopamine molecule. To use a different molecule, download the .mol file for that molecule from the `list of molecules <http://www.biotopics.co.uk/jsmol/molecules/>`_ on the `BioTopics <http://www.biotopics.co.uk/>`_ website. Then, upload the .mol file to the **Files & Uploads** page for your course in Studio, and change "Molecules_Dopamine.mol" in the example code to the name of your .mol file.

To create the molecule editor that appears in the image above, you need an HTML component followed by a Problem component.

#. Upload all of the files listed above to the **Files & Uploads** page in your course.
#. Create the HTML component.
  #. In the unit where you want to create the problem, click **HTML** under **Add New Component**, and then click **HTML**.
  #. In the component that appears, click **Edit**.
  #. In the component editor, paste the HTML component code from below.
  #. Make any changes that you want, and then click **Save**.
#. Create the Problem component.
  #. Under the HTML component, click **Problem** under **Add New Component**, and then click **Blank Advanced Problem**.
  #. In the component that appears, click **Edit**.
  #. In the component editor, paste the Problem component code from below.
  #. Make any changes that you want, and then click **Save**.

.. _EMC Problem Code:

=====================
Molecule Editor Code
=====================

To create the molecule editor, you need an HTML component and a Problem component.

HTML Component Code
-------------------

::

  <h2>Molecule Editor</h2>
  <p>The molecule editor makes creating and visualizing molecules easy. A chemistry professor may have you build and submit a molecule as part of an exercise.</p>
  <div>
  <script type="text/javascript">// <![CDATA[
  function toggle2(showHideDiv, switchTextDiv) {
              var ele = document.getElementById(showHideDiv);
              var text = document.getElementById(switchTextDiv);
              if(ele.style.display == "block") {
                  ele.style.display = "none";
                  text.innerHTML = "+ open";
                  }
              else {
                  ele.style.display = "block";
                  text.innerHTML = "- close";
              }
          }
  // ]]></script>
  </div>
  <div>
  <style type="text/css"></style>
  </div>
  <div id="headerDiv">
  <div id="titleText">Using the Molecule Editor<a id="myHeader" href="javascript:toggle2('myContent','myHeader');">+ open </a></div>
  </div>
  <div id="contentDiv">
  <div id="myContent" style="display: none;">
  <p>In this problem you will edit a molecule using the molecular drawing program shown below:</p>
  <img alt="" src="/static/MoleculeEditor_HTML.png" /></div>
  </div>
  <p>&nbsp;</p>
  <div id="headerDiv">
  <div id="titleText">Are the molecules I've drawn chemically possible?<a id="IntroductionHeader" href="javascript:toggle2('IntroductionContent','IntroductionHeader');">+ open </a></div>
  </div>
  <div id="contentDiv">
  <div id="IntroductionContent" style="display: none;">
  <p>The chemical editor you are using ensures that the structures you draw are correct in one very narrow sense, that they follow the rules for covalent bond formation and formal charge. However, there are many structures that follow these rules that are chemically impossible, unstable, do not exist in living systems, or are beyond the scope of this course. The editor will let you draw them because, in contrast to the rules of formal charge, these properties cannot be easily and reliably predicted from structures.</p>
  <p>If you submit a structure that includes atoms that are not possible or are beyond the scope of this course, the software will warn you specifically about these parts of your structure and you will be allowed to edit your structure and re-submit. Submitting an improper structure will not count as one of your tries. In general, you should try to use only the atoms most commonly cited in this course: C, H, N, O, P, and S. If you want to learn about formal charge, you can play around with other atoms and unusual configurations and look at the structures that result.</p>
  </div>
  </div>
  <div id="ap_listener_added">&nbsp;</div>

Problem Component
-----------------

**Problem 1**

.. warning:: Jean-Michel: The code for Problem 3 is the code that's in the problem in the demo course (except that I changed the name of the dopamine.mol file to Dopamine_Molecule.mol). Is it still usable?  (If not, no big deal.) 
  
    Also, can you supply sample text for the two sample problems you've provided? (For the first one, for example, it could just be "The dopamine molecule, as shown, cannot make strong hydrogen bonds. Edit the dopamine molecule so that it can make strong hydrogen bonds." But I'm not sure what the second one is trying to do.)

    In problems 1 and 2, the file path is "/static/**molecules**/dopamine.mol". Should this just be "static/dopamine.mol"?

    And one more thing: Problem 3 includes an answer. Do we want to do that for the other problems?

::

  <problem>
  <p>The dopamine molecule, as shown, cannot make ionic bonds. Edit the dopamine molecule so it can make ionic bonds.</p>
  <p>When you are ready, click Check. If you need to start over, click Reset.</p>
    <script type="loncapa/python">
  def check1(expect, ans):
      import json
      mol_info = json.loads(ans)["info"]
      return any(res == "Can Make Ionic Bonds" for res in mol_info)
      </script>
    <customresponse cfn="check1">
      <editamoleculeinput file="/static/Molecules_Dopamine.mol">
          </editamoleculeinput>
    </customresponse>
    <solution>
      <img src="/static/MoleculeAnswer.png"/>
    </solution>
  </problem>

**Problem 2**

::

  <problem>
  <script type="loncapa/python">
  def grader_1(expect, ans):
      import json
      mol_info = json.loads(ans)["info"]
      return any(res == "Cannot Make Strong Hydrogen Bonds" for res in mol_info)
  </script>
    <customresponse cfn="grader_1">
      <editamoleculeinput file="/static/molecules/dopamine.mol">
      </editamoleculeinput>
    </customresponse>
  </problem>

**Problem 3**

::

  <problem">
  <script type="loncapa/python">
  def grader_2(expect, ans):
      import json
      mol_info = json.loads(ans)["info"]

      hydrophobicity_index_str=mol_info[0]
      hydrophobicity_index=float(hydrophobicity_index_str[23:])
      return hydrophobicity_index &gt; .490
  </script>
    <customresponse cfn="grader_2">
      <editamoleculeinput file="/static/molecules/dopamine.mol">
      </editamoleculeinput>
  </customresponse>
  </problem>

.. _Multiple Choice and Numerical Input:

*******************************************
Multiple Choice and Numerical Input Problem
*******************************************

You can create a problem that combines a multiple choice and numerical input problems. Students not only select a response from options that you provide, but also provide more specific information, if necessary.

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
Protex Protein Builder
************************

The Protex protein builder asks students to create specified protein shapes by stringing together amino acids. In the example below, the goal protein shape is a simple line. 


.. image:: /Images/ProteinBuilder.gif
  :alt: Image of the protein builder

.. _Create the Protein Builder:

==========================
Create the Protein Builder
==========================

To create the protein builder:

#. Under **Add New Component**, click **Problem**, and then click **Blank Advanced Problem**.
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
