.. _The Structure of edX-Insider:

#############################
The Structure of edX-Insider
#############################

This chapter describes the structure of a the edX_Insider course. See:

*

For information on how a generic OLX course is structures, see :ref:`ODL
Directory Structure`.


******************************************
edX-Insider and Directory File Structures
******************************************

All files and subdirectores that comprise edX-Insider are stored in the
`Ongoing`_ directory in the edX-Insider Git repository.

SCREEN SHOT FROM GITHUB


******************************************
edX-Insider and Directory File Structures
******************************************



********************
Top-level Directory
********************


********************
XBLock Directories
********************


********************
Platform Directories
********************

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

* ``handouts.html``, which contains the contain for the Course Handouts page in
  the course.

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





.. include:: ../links.rst