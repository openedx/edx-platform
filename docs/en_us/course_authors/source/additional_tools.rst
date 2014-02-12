.. _Additional Tools:


#############################
Additional Tools
#############################

*************************
Additional Tools Overview
*************************

Individual course teams frequently create tools and problem types that don't have templates in Studio. We want to make these tools available to all our course teams. We provide you with all the files and code that you need to create these problems in Studio.

Below, you'll find the information you need to create the following tools.

* :ref:`Interactive Periodic Table`
* :ref:`Molecule Editor`
* :ref:`Multiple Choice and Numerical Input`
* :ref:`Protein Builder`

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

Students can use the molecule editor to learn how to create molecules. The molecule editor allows students to draw molecules that follow the rules for covalent bond formation and formal charge, but are chemically impossible. The molecule editor warns students if they try to submit a structure that is not possible.

.. image:: /Images/Molecule_Editor.gif
  :alt: Image of the molecule editor

.. _Create the Molecule Editor:

==========================
Create the Molecule Editor
==========================

To create a molecule editor, you need the following files:

* Molecules_Dopamine.mol
* MoleculeAnswer.png
* MoleculeEditor_HTML.png

To download all of these files in a .zip archive, go to http://files.edx.org/MoleculeEditorFiles.zip.

To create the molecule editor, you need an HTML component followed by a Problem component.

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

To create the molecule editor, you'll need an HTML component followed by a Problem component.

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
  <p>The JME molecular editor is provided courtesy of Peter Ertl and Novartis; the licence can be found <a href="/static/data/license.txt">here.</a></p>
  </div>
  </div>
  <div id="ap_listener_added">&nbsp;</div>



Problem Component
-----------------
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
      <editamoleculeinput file="/static/dopamine.mol">
          </editamoleculeinput>
    </customresponse>
    <solution>
      <img src="/static/Molecule.jpg"/>
    </solution>
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
