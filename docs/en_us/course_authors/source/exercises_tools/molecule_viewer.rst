.. _Molecule Viewer:

#######################
Molecule Viewer Tool
#######################

Studio offers two tools that you can use in discussions of molecules:

* With the **molecule viewer** tool, you can create three-dimensional representations of molecules for students to view. 
* With the **molecule editor** problem type, you can allow students to draw their own molecules. For more information about this tool, see :ref:`Molecule Editor`.

Both tools use **JSmol**, a JavaScript-based molecular viewer from Jmol. (You don't need to download this tool; Studio uses it automatically.) For more information about JSmol, see `JSmol <http://sourceforge.net/projects/jsmol/>`_.

The following image shows the molecule viewer tool in a course:

.. image:: /Images/MoleculeViewer.png
   :width: 500
   :alt: Image of molecule viewer showing a molecule of Ciprofloxacin



.. note:: To create a molecule viewer tool, you must have permission to upload files to a third-party file hosting site such as Amazon Web Services Simple Storage Service (AWS S3). When you create the molecule viewer, you'll upload a folder that contains a large number of files to the file hosting site. 

.. _Create the Molecule Viewer:

*******************************
Create the Molecule Viewer Tool
*******************************

Creating a molecule viewer tool has several steps:

#. Download files from the `BioTopics website <http://www.biotopics.co.uk/jsmol/molecules>`_ and from edX.
#. Move or edit some of the files that you downloaded.
#. Upload a folder that contains all of the files that you downloaded and edited to your own file hosting site.
#. Create an HTML component that contains an IFrame in Studio. The IFrame references the files that you upload to the file hosting site.

================================================
Download Files from BioTopics and edX
================================================

#. Create or download a .mol file for the molecule that you want to show. You can download a variety of .mol files from the `BioTopics website <http://www.biotopics.co.uk/jsmol/molecules>`_. Save the file in a place where you can easily find it.
#. Download the `MoleculeViewerFiles.zip <http://files.edx.org/MoleculeViewerFiles.zip>`_ file from edX.
#. Unzip the `MoleculeViewerFiles.zip <http://files.edx.org/MoleculeViewerFiles.zip>`_ file that you've downloaded.

   When you unzip the file, you'll see a **MoleculeViewerFiles** folder that contains the following folders and files:

    * data (folder)
    * j2s (folder)
    * js (folder)
    * MoleculeViewer.html (file)

================================================================
Move the .mol File and Edit the MoleculeViewer.html File
================================================================

#. Move the .mol file that you downloaded from BioTopics into the **data** folder that you downloaded from edX.
#. Edit the MoleculeViewer.html file:

   #. In a text editor, open the MoleculeViewer.html file.
   #. In line 19 of the MoleculeViewer.html file, change **Example.mol** to the name of your .mol file. For example, if you downloaded the Glucose.mol file, line 19 in your file will look like the following:

   		``script: "set antialiasDisplay; background black; load data/Glucose.mol;"``

3. Save the MoleculeViewer.html file.

================================
Upload Files to a Hosting Site
================================

#. Make sure that your **MoleculeViewerFiles** folder contains the following folders and files:

   * data (folder): Earlier, you added a .mol file to this folder.
   * j2s (folder)
   * js (folder)
   * MoleculeViewer.html (file): Earlier, you changed line 19 in this file.

2. Upload the entire **MoleculeViewerFiles** folder to your file hosting site. 

   .. note:: Because this folder contains many files, uploading the folder may take several minutes, even over a fast connection.

===============================
Create a Component in Studio
===============================

#. In Studio, open the unit where you want to add the molecule viewer.
#. Under **Add New Component**, click **HTML**, and then click **IFrame**.
#. In the component editor that opens, replace the existing content with your own text.
#. In the toolbar, click **HTML**.
#. In the **HTML Source Code** box, enter the following line in the place where you want the molecule viewer to appear:

   ``<p><iframe name="moleculeiframe" src="https://path_to_folder/MoleculeViewerFiles/MoleculeViewer.html" width="500" height="500"></iframe></p>``

6. Replace ``path_to_file`` with the URL of your file hosting site. For example, the line may look like the following:

   ``<p><iframe name="moleculeiframe" src="https://myfiles.example.com/MoleculeViewerFiles/MoleculeViewer.html" width="500" height="500"></iframe></p>``

7. Click **OK** to close the **HTML Source Code** box, and then click **Save** to save the component.
#. Click **Preview** to see your component as a student would see it.