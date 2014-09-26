.. _Molecule Editor:

########################
Molecule Editor Problem
########################

Studio offers two tools that you can use in discussions of molecules:

* With the **molecule viewer**, you can create three-dimensional representations of molecules for students to view. For more information about this tool, see :ref:`Molecule Viewer`.
* With the **molecule editor**, you can allow students to draw their own molecules. 

Both tools use **JSmol**, a JavaScript-based molecular viewer from Jmol. In addition, the molecule editor problem type uses the JSME molecule editor created by Peter Erl and Bruno Bienfait. (You don't need to download either of these tools; Studio uses them automatically.) For more information about JSmol, see `JSmol <http://sourceforge.net/projects/jsmol/>`_. For more information about the JSME molecule editor, see `JSME Molecule Editor <http://peter-ertl.com/jsme/index.html>`_.

Students can use the molecule editor to learn how to create molecules. The molecule editor allows students to draw molecules that follow the rules for covalent bond formation and formal charge, even if the molecules are chemically impossible, are unstable, or do not exist in living systems. The molecule editor warns students if they try to submit a structure that is chemically impossible.

.. image:: /Images/Molecule_Editor.png
  :width: 500
  :alt: Image of the molecule editor

.. _Create the Molecule Editor:

******************************
Create the Molecule Editor
******************************

To create a molecule editor problem:

#. Under **Add New Component**, click **Problem**, and then click **Molecular Structure**.
#. In the component that appears, click **Edit**.
#. In the component editor, modify the code to correspond to your problem.
#. Click **Save**.

.. _EMC Problem Code:

========================
Molecule Editor Code
========================

.. code-block:: xml

  <problem>
    <p>
      A molecular structure problem lets the user use the JSME editor
      component to draw a new molecule or update an existing drawing and then
      submit their work.  Answers are specified as SMILES strings.
    </p>
    <p>
      I was trying to draw my favorite molecule, caffeine. Unfortunately,
      I'm not a very good biochemist. Can you correct my molecule?
    </p>
    <jsmeresponse>
      <jsme>
          <!-- 
             You can set initial state of the editor by including a molfile
             inside of the jsme tag. 
             
             Take care that indentation is preserved.  The molfile format is
             sensitive to whitespace, so the best policy is to cut and paste
             as-is on a new line without adjusting the indentation.  If you
             do indent the molfile data, make sure every line is indented the
             same amount using space characters only, no tabs.
          -->
          <initial-state>
              CN2Cc1[nH]cnc1N(C)C2=O
              JME 2014-06-28 Wed Jul 23 13:41:18 GMT-400 2014
               
               12 13  0  0  0  0  0  0  0  0999 V2000
                  3.6373    2.1000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  3.6373    3.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  2.4249    4.2000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  1.2124    3.5000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
                  1.2124    2.1000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  2.4249    1.4000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
                  4.9688    1.6674    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
                  5.7917    2.8000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  4.9688    3.9326    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
                  0.0000    1.4000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
                  0.0000    4.2000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                  2.4249    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
                1  2  2  0  0  0  0
                2  3  1  0  0  0  0
                3  4  1  0  0  0  0
                4  5  1  0  0  0  0
                5  6  1  0  0  0  0
                6  1  1  0  0  0  0
                7  8  2  0  0  0  0
                8  9  1  0  0  0  0
                2  9  1  0  0  0  0
                1  7  1  0  0  0  0
                5 10  2  0  0  0  0
                4 11  1  0  0  0  0
                6 12  1  0  0  0  0
              M  END
          </initial-state>
          <!-- Answers are specified as SMILES strings. -->
          <answer>Cn1cnc2c1c(=O)n(C)c(=O)n2C</answer>
      </jsme>
      <!-- This answer is shown to the student when they click the 
           "Show Answer" button in the UI.  It is not used for grading and 
           should be human readable. -->
      <answer>C8H10N4O2</answer>
    </jsmeresponse>
    <solution>
      <div class="detailed-solution">
        <p>Explanation</p>
        <p>
          Some scholars have hypothesized that the renaissance was made
          possible by the introduction of coffee to Italy.  Likewise scholars
          have linked the Enlightenment with the rise of coffee houses in
          England.  
        </p>
      </div>
    </solution>
  </problem>
