.. _ODL Directory Structure:

###############################################
OLX Course Structure
###############################################

This chapter describes the structure of a generic OLX course. See:

* `OLX and Directory File Structures`_
* `Top-level Directory`_
* `XBlock directories`_
* `edX Platform Directories`_

See :ref:`The Structure of edX-Insider` for information on how a specific OLX course is structured.


****************************************
OLX and Directory File Structures
****************************************

All files and sub-directories that comprise your OLX course are stored within
a single directory.

OLX provides for some flexibility in the directory and file structure
you use to build your course.

************************
Top-level Directory
************************

Starting out, it is easiest to create your courseware structure in a
single file, the ``course.xml file``. 

This file can contain your entire course, but in most cases, it is convenient
to split out large chunks of content into individual files. This is typically
done either at the level of large components, such as problems or homework
assignments.

Currently, when Studio exports a course, it places each component in its own
file. 

For example, the edX Platform contains a directory called
`manual-testing-complete`_ that contains a course with all component
types for testing purposes.

Following are descriptions of directories needed for a typical course. You
should set up these directories in preparation for developing your course
content.

.. note::
 If you are using custom XBlocks, you can have
 additional directories that store the XML for XBlocks of that type.

*******************
XBlock Directories
*******************

edX course components can be broken out of the main ``course.xml`` file
into individual files. Those files go into directories of the name of
the component type (XML tag). For example, components of type ``html``
can be placed as individual files in the ``html`` directory. If your
course does not contain html files, or if they are all embedded in
their top-level components, you do not need to create an ``html``
directory.

For information about several examples of these directories, see: 

See :ref:`HTML Components` for more information.
See :ref:`Problems and Tools` for more information.
See :ref:`Video Components` for more information.

As the set of XBlocks grows, so does the set of associated XML tags
and directories.

*************************
edX Platform Directories
*************************

In addition to the course hierarchy, which is designed to be generic
and cross-platform, OLX courses contain a set of JSON and HTML
files that specify course policies and non-courseare content.

====================
``about`` Directory
====================

The ``about`` directory contains:

* ``overview.html``, which contains the content for the course overview page
  that students see in the the Learning Management System (LMS).

* ``short_description.html``, which contains the content for the course in the
  course list.

See :ref:`The Course About Pages` for more information.


====================
``info`` Directory
====================

The ``info`` directory contains:

* ``handouts.html``, which contains the content for the **Course Handouts**
  page in the course.

* ``updates.html``, which contains the course updates students see when opening
  a course.

=======================
``policies`` Directory
=======================

The ``policies`` directory contains:

* ``grading_policy.json``, which defines how student work is graded in the
  course.

* ``policy.json``, which defines various settings in the course.

* ``assets.json``, which defines all files used in the course, such as images.
  
See :ref:`Course Policies` for more information.

====================
``static`` Directory
====================

The ``static`` directory contains the files used in your course, such as images
or PDFs.

See :ref:`Course Assets` for more information.

====================
``tabs`` Directory
====================

The ``tabs`` directory contains an HTML file for each page you add to your
course.

See :ref:`Course Tabs` for more information.

 .. include:: links.rst
