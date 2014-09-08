.. _ODL Directory Structure with edX Studio:

###############################################
OLX Directory Structure
###############################################

See:

* `OLX and Directory File Structures`_
* `Top-level Directory`_
* `about Directory`_
* `html Directory`_
* `info Directory`_
* `policies Directory`_
* `problem Directory`_
* `static Directory`_
* `tabs Directory`_
* `video Directory`_



****************************************
OLX and Directory File Structures
****************************************

All files and sub-directories that comprise your OLX course are stored within
a single directory.

OLX provides for flexibility in the directory and file structure you use to
build your course.

************************
Top-level Directory
************************

In most cases, it is easiest to create your courseware structure in a
single file, the ``course.xml file``. 

The ``course.xml`` file would contain the
definition of all chapters (sections), sequentials (subsections), and verticals
(units) in your courseware. The courseware structure would then refer to files
for components, which are stored in a directory for each type of XBlock.

For example, the edX Platform contains a directory called `manual-testing-complete`_ that contains a course with all component types for testing
purposes.

Course content, other than the courseware, is stored in separate directories
and files as shown in the rest of this chapter.

Following are descriptions of directories needed for a typical course. You
should set up these directories in preparation for developing your course
content.

.. note::
 If you are using custom XBlocks, you can have
 additional directories that store the XML for XBlocks of that type.

********************
``about`` Directory
********************

The ``about`` directory contains:

* ``overview.html``, which contains the content for the course overview page
  students see the the Learning Management System (LMS).

* ``short_description.html``, which contains the content for the course in the
  course list.

See :ref:`The Course About Pages` for more information.


********************
``html`` Directory
********************

The ``html`` directory contains an HTML file for each HTML component in
the course.

If you do not need HTML components in the course, you do not need to create
this directory.

See :ref:`HTML Components` for more information.

********************
``info`` Directory
********************

The ``info`` directory contains:

* ``handouts.html``, which contains the contain for the Course Handouts page in
  the course.

* ``updates.html``, which contains the course updates students see when opening
  a course.

***********************
``policies`` Directory
***********************

The ``policies`` directory contains:

* ``grading_policy.json``, which defines how student work is graded in the
  course.

* ``policy.json``, which defines various settings in the course.

* ``assets.json``, which defines all files used in the course, such as images.
  
See :ref:`Course Policies` for more information.

**********************
``problem`` Directory
**********************

The ``problem`` directory contains an XML file for each problem component you
use in your course.

If you do not need problem components in the course, you do not need to create
this directory.

See :ref:`Problems and Tools` for more information.

********************
``static`` Directory
********************

The ``static`` directory contains the files used in your course, such as images
or PDFs.

See :ref:`Course Assets` for more information.

********************
``tabs`` Directory
********************

The ``tabs`` directory contains an HTML file for each page you add to your
course.

See :ref:`Course Pages` for more information.

********************
``video`` Directory
********************

The ``video`` directory contains an XML file for each video component you use
in your course.

If you do not need video components in the course, you do not need to create
this directory.

See :ref:`Video Components` for more information.

 .. include:: links.rst