.. _The Structure of edX-Insider:

#############################
The Structure of edX-Insider
#############################

This chapter describes the structure of a the edX_Insider course. See:

* `edX-Insider and Directory File Structures`_
* `Top-level Directory`_
* `The HTML XBlock Directory`_
* `Platform Directories`_

For information on how a generic OLX course is structures, see :ref:`ODL
Directory Structure`.

.. note:: 
  The structure and content of edX-Insider may change before this documentation
  is updated.

******************************************
edX-Insider and Directory File Structures
******************************************

All files and subdirectores that comprise edX-Insider are stored in the
`Ongoing`_ directory in the edX-Insider Git repository.

SCREEN SHOT FROM GITHUB



********************
Top-level Directory
********************

The `Ongoing`_ directory in the edX-Insider Git repository contains the
``course.xml`` file as well as XBlock and Platform directories.

The `course.xml`_ file contains the XML for the courseware. All chapters and
sequentials are defined in ``course.xml``.

Most and verticals are defined in ``course.xml``; two verticals are referenced
in other files.

The content of some HTML XBlocks is embedded within ``course.xml``; other HTML
XBlocks are referenced in other files.

Problems are referenced in other files.

See :ref:`The edX-Insider course.xml File` for more information.


******************************
The HTML XBlock Directory
******************************

While some HTML content is embedded in ``course.xml``, many HTML XBlocks are
stored as separate files in the ``HTML`` directory.

==============================
Example of a Referenced XBlock
==============================

You can reference an XBlock from the ``course.xml`` file. You may do this, for
example, to reuse that content in multiple locations in your course, or in
multiple courses.

For example, in ``course.xml``, the first vertical in the courseware contains a
single HTML XBlock with the display name ``Week overview``, which references
``Week_overview`` in the ``url_name`` attribute:

.. code-block:: html
  
  <chapter display_name="Pedagogical Foundations: Constructive Learning"  
      url_name="Week_2_Technology_enabled_constructive_learning">
      <sequential format="Learning Sequence" graded="true" 
          display_name="Overview (go here first)" 
          url_name="Overview_go_here_first">
          <vertical display_name="Week's overview" url_name="Week_s_overview">
              <html display_name="Week overview" filename="Week_overview" 
                  url_name="Week_overview"/>

There is a file called ``Week_overview.html`` in the ``html`` directory that
contains the content for that HTML component. For detailed information, see the
`Week_overview.html`_ file in GitHub.

For a student, that HTML component appears as the first unit of the course:

SCREEN SHOT


==============================
Example of an Inline XBlock
==============================

You can include an XBlock content within the ``course.xml`` file. You may do
this for ease of reading and maintenance when you do not need to reuse the
content.

For example, in ``course.xml``, within the sequential with the display name
``In-class exercise``, there is embedded HTML content:

.. code-block:: html
  
  <sequential display_name="In-class exercise" url_name="in_class"> 
      <html display_name="Overview" url_name="overview"> 
          <p>In the on-line portion,
             we examined a way we used technology to allow efficient 
             implementation of one theory from learning science – constructive 
             learning – in edX. In designing the edX platform, we applied many 
             such techniques. We took aspects of mastery learning, project-
             based learning, gamification and others. Other platforms have 
             sophisticated techniques for targeting specific student 
             misconceptions, enabling a range of student social experiences, 
             assessing teacher performance, and hundreds of other research-
             based techniques. We would like to give you a chance to practice
             with designing software to enable good pedagogy. 
          </p>
	      . . .
      </html>

For a student, that HTML component appears as unit of the course in the same way as a referenced HTML component does:

SCREEN SHOT


********************
Platform Directories
********************

The edX-Insider course contains information in the platform directories as
described below.

====================
``about`` Directory
====================

The ``about`` directory contains:

* ``overview.html``, which contains the content for the course overview page
  students see the the Learning Management System (LMS).

* ``short_description.html``, which contains the content for the course in the
  course list.

See :ref:`The Course About Pages` for more information.


====================
``info`` Directory
====================

The ``info`` directory contains:

* ``handouts.html``, which contains the content for the Course Handouts page in
  the course.

* ``updates.html``, which contains the course updates students see when opening
  a course.

  ????UPDATES JSON????

=======================
``policies`` Directory
=======================

The ``policies`` directory contains:

* ``assets.json``, which defines all files used in the course, such as images.

* A directory, ``Ongoing`` for the course, which contains:

  * ``grading_policy.json``, which defines how student work is graded in the
    course.

  * ``policy.json``, which defines various settings in the course.
  
See :ref:`Course Policies` for more information.

====================
``static`` Directory
====================

The ``static`` directory contains the files used in the course, such as images
or PDFs.

See :ref:`Course Assets` for more information.

=======================
``vertical`` Directory
=======================

The ``vertical`` directory contains the XML for two verticals used in the
course:

* The ``constructive_ora_exercise.xml`` file
* The ``in_class_ora.xml`` file

You have the option of embedding verticals in the ``course.xml`` file, and in
most cases this is the most straightforward option. However, OLX give you the
option to store XML for verticals in separate files in the ``vertical``
directory.

In this case, IS THERE A GOOD REASON ORA VERTICALS ARE SEPARATE?

The vertical files are references in ``course.xml`` as follows:

.. code-block:: html
  
  <vertical url_name="constructive_ora_exercise"></vertical>

And:

.. code-block:: html
  
  <vertical url_name="in_class_ora"></vertical>

The vertical files contain XML that defines open response assessments. See
`Creating a Peer Assessment`_ for more information.



.. include:: ../links.rst