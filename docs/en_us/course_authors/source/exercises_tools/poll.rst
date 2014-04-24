
.. _Poll:

##########
Poll Tool
##########

You can run polls in your course so that your students can share opinions on different questions.

.. image:: /Images/PollExample.png

.. note:: Creating a poll requires you to export your course, edit some of your course's XML files in a text editor, and then re-import your course. We recommend that you create a backup copy of your course before you create the poll. We also recommend that you only edit the files that will contain polls in the text editor if you're very familiar with editing XML. 

**************
Terminology
**************

Sections, subsections, units, and components have different names in the **Course Outline** view and in the list of files that you'll see after you export your course and open the .xml files for editing. The following table lists the names of these elements in the **Course Outline** view and in a list of files.

.. list-table::
   :widths: 15 15
   :header-rows: 0

   * - Course Outline View
     - File List
   * - Section
     - Chapter
   * - Subsection
     - Sequential
   * - Unit
     - Vertical
   * - Component
     - Discussion, HTML, problem, or video

For example, when you want to find a specific section in your course, you'll look in the **Chapter** folder when you open the list of files that your course contains. To find a unit, you'll look in the **Vertical** folder.

.. _Create a Poll:

**************
Create a Poll
**************

#. In the unit where you want to create the poll, create components that contain all the content that you want *except* for the poll. Make a note of the 32-digit unit ID that appears in the **Unit Identifier** field under **Unit Location**.

#. Export your course. For information about how to do this, see :ref:`Exporting and Importing a Course`. Save the .tar.gz file that contains your course in a memorable location so that you can find it easily.

#. Locate the .tar.gz file that contains your course, and then unpack the .tar.gz file so that you can see its contents in a list of folders and files.

   - To do this on a Windows computer, you'll need to download a third-party program. For more information, see `How to Unpack a tar File in Windows <http://www.haskell.org/haskellwiki/How_to_unpack_a_tar_file_in_Windows>`_, `How to Extract a Gz File <http://www.wikihow.com/Extract-a-Gz-File>`_, `The gzip Home Page <http://www.gzip.org/>`_, or the `Windows <http://www.ofzenandcomputing.com/how-to-open-tar-gz-files/#windows>`_ section of the `How to Open .tar.gz Files <http://www.ofzenandcomputing.com/how-to-open-tar-gz-files/>`_ page.

   - For information about how to do this on a Mac, see the `Mac OS X <http://www.ofzenandcomputing.com/how-to-open-tar-gz-files/#mac-os-x>`_ section of the `How to Open .tar.gz Files <http://www.ofzenandcomputing.com/how-to-open-tar-gz-files/>`_ page.

#. In the list of folders and files, open the **Vertical** folder. 

   .. note:: If your unit is not published, open the **Drafts** folder, and then open the **Vertical** folder in the **Drafts** folder.

#. In the **Vertical** folder, locate the .xml file that has the same name as the unit ID that you noted in step 1, and then open the file in a text editor such as Sublime 2. For example, if the unit ID is e461de7fe2b84ebeabe1a97683360d31, you'll open the e461de7fe2b84ebeabe1a97683360d31.xml file.

   The file contains a list of all the components in the unit, together with the URL names of the components. For example, the following file contains an HTML component followed by a Discussion component.

   .. code-block:: xml
     
       <vertical display_name="Test Unit">
        <html url_name="b59c54e2f6fc4cf69ba3a43c49097d0b"/>
        <discussion url_name="8320c3d511484f3b96bdedfd4a44ac8b"/>
       </vertical>

#. Add the following poll code in the location where you want the poll. Change the text of the prompt to the text that you want.

   .. code-block:: xml
      
    <poll_question display_name="Poll Question">
      <p>Text of the prompt</p>
      <answer id="yes">Yes</answer>
      <answer id="no">No</answer>
    </poll_question>

   In the example above, if you wanted your poll to appear between the HTML component and the Discussion component in the unit, your code would resemble the following.

   .. code-block:: xml

     <vertical display_name="Test Unit">
      <html url_name="b59c54e2f6fc4cf69ba3a43c49097d0b"/>
      <poll_question display_name="Poll Question">
        <p>Text of the prompt</p>
        <answer id="yes">Yes</answer>
        <answer id="no">No</answer>
      </poll_question>
      <discussion url_name="8320c3d511484f3b96bdedfd4a44ac8b"/>
     </vertical>

#. After you add the poll code, save and close the .xml file.

#. Re-package your course as a .tar.gz file.

   * For information about how to do this on a Mac, see `How to Create a Tar GZip File from the Command Line <http://osxdaily.com/2012/04/05/create-tar-gzip/>`_.

   * For information about how to do this on a Windows computer, see `How to Make a .tar.gz on Windows <http://stackoverflow.com/questions/12774707/how-to-make-a-tar-gz-on-windows>`_.

#. In Studio, re-import your course. You can now review the poll question and answers that you added in Studio.

.. note::

  * Although polls render correctly in Studio, you cannot edit them in Studio. You will need to follow the export/import process outlined above to make any edits to your polls.
  
  * A .csv file that contains student responses to the problem is not currently available for polls. However, you can obtain the aggregate data directly in the problem.  

*********************
Format description
*********************

The main tag of Poll module input is:

.. code-block:: xml

    <poll_question> ... </poll_question>

``poll_question`` can include any number of the following tags:
any xml and ``answer`` tag. All inner xml, except for ``answer`` tags, we call "question".

==================
poll_question tag
==================

Xmodule for creating poll functionality - voting system. The following attributes can
be specified for this tag::

    name - Name of xmodule.
    [display_name| AUTOGENERATE] - Display name of xmodule. When this attribute is not defined - display name autogenerate with some hash.
    [reset | False] - Can reset/revote many time (value = True/False)

============
answer tag
============

Define one of the possible answer for poll module. The following attributes can
be specified for this tag::

    id - unique identifier (using to identify the different answers)

Inner text - Display text for answer choice.

***********
Example
***********

==================
Example of poll
==================

.. code-block:: xml

    <poll_question name="second_question" display_name="Second question">
        <h3>Age</h3>
        <p>How old are you?</p>
        <answer id="less18">&lt; 18</answer>
        <answer id="10_25">from 10 to 25</answer>
        <answer id="more25">&gt; 25</answer>
    </poll_question>

================================================
Example of poll with unable reset functionality
================================================

.. code-block:: xml

    <poll_question name="first_question_with_reset" display_name="First question with reset"
        reset="True">
        <h3>Your gender</h3>
        <p>You are man or woman?</p>
        <answer id="man">Man</answer>
        <answer id="woman">Woman</answer>
    </poll_question>