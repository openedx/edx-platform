.. _Molecule Editor:

#######################
Molecule Editor Tool
#######################

Students can use the molecule editor to learn how to create molecules. The molecule editor allows students to draw molecules that follow the rules for covalent bond formation and formal charge, even if the molecules are chemically impossible, are unstable, or do not exist in living systems. The molecule editor warns students if they try to submit a structure that is chemically impossible.

The molecule editor incorporates two tools: the JSME molecule editor created by Peter Erl and Bruno Bienfait, and JSmol, a JavaScript-based molecular viewer from Jmol. (You don't need to download either of these tools--Studio uses them automatically.) For more information about the JSME molecule editor, see `JSME Molecule Editor <http://peter-ertl.com/jsme/index.html>`_. For more information about JSmol, see `JSmol <http://sourceforge.net/projects/jsmol/>`_.

.. image:: /Images/Molecule_Editor.png
  :alt: Image of the molecule editor

.. _Create the Molecule Editor:

******************************
Create the Molecule Editor
******************************

To create a molecule editor, you need the following files:

* MoleculeAnswer.png
* MoleculeEditor_HTML.png
* dopamine.mol

To download all of these files in a .zip archive, go to http://files.edx.org/MoleculeEditorFiles.zip.

.. note:: The molecule that appears when the tool starts is a dopamine molecule. To use a different molecule, download the .mol file for that molecule from the `list of molecules <http://www.biotopics.co.uk/jsmol/molecules/>`_ on the `BioTopics <http://www.biotopics.co.uk/>`_ website. Then, upload the .mol file to the **Files & Uploads** page for your course in Studio, and change "dopamine.mol" in the example code to the name of your .mol file.

To create the molecule editor that appears in the image above, you need an HTML component followed by a Problem component.

#. Upload all of the files listed above to the **Files & Uploads** page in your course.
#. Create the HTML component.

  #. In the unit where you want to create the problem, click **HTML** under **Add New Component**, and then click **HTML**.
  #. In the component that appears, click **Edit**.
  #. In the component editor, paste the HTML component code from below.
  #. Make any changes that you want, and then click **Save**.

3. Create the Problem component.

  #. Under the HTML component, click **Problem** under **Add New Component**, and then click **Blank Advanced Problem**.
  #. In the component that appears, click **Edit**.
  #. In the component editor, paste the Problem component code from below.
  #. Click **Save**.

.. _EMC Problem Code:

========================
Molecule Editor Code
========================

To create the molecule editor, you need an HTML component and a Problem component.

HTML Component Code
***************************

.. code-block:: xml

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




Problem Component Code
***************************

.. code-block:: xml

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
      <img src="/static/MoleculeAnswer.png"/>
    </solution>
  </problem>

**Problem 2**

::

  <problem>
  <p>The dopamine molecule, as shown, cannot make strong hydrogen bonds. Edit the dopamine molecule so that it can make strong hydrogen bonds.</p>
  <script type="loncapa/python">
  def grader_1(expect, ans):
      import json
      mol_info = json.loads(ans)["info"]
      return any(res == "Cannot Make Strong Hydrogen Bonds" for res in mol_info)
  </script>
    <customresponse cfn="grader_1">
      <editamoleculeinput file="/static/dopamine.mol">
      </editamoleculeinput>
    </customresponse>
  </problem>

**Problem 3**

::

  <problem>
  <p>The dopamine molecule has an intermediate hydrophobicity. Edit the dopamine molecule so that it is more hydrophobic.</p>
  <script type="loncapa/python">
  def grader_2(expect, ans):
      import json
      mol_info = json.loads(ans)["info"]

      hydrophobicity_index_str=mol_info[0]
      hydrophobicity_index=float(hydrophobicity_index_str[23:])
      return hydrophobicity_index &gt; .490
  </script>
    <customresponse cfn="grader_2">
      <editamoleculeinput file="/static/dopamine.mol">
      </editamoleculeinput>
  </customresponse>
  </problem>