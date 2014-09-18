.. _Exporting and Importing a Course:

#####################################
Exporting and Importing a Course
#####################################

You can :ref:`Export a Course` and :ref:`Import a Course` through Studio.

.. _Export a Course:

***************
Export a Course
***************

There are several reasons you may want to export your course:

* To save your work
* To edit the XML in your course directly
* To create a backup copy of your course, which you can import if you want to
  revert the course back to a previous state
* To create a copy of your course that you can later import into another course
  instance and customize
* To share with another instructor for another class
 
 
When you export your course, Studio creates a **.tar.gz** file that includes
the following course data:
 
* Course content (all Sections, Subsections, and Units)
* Course structure
* Individual problems
* Pages
* Course assets
* Course settings
 

The following data is not exported with your course:
 
* User data
* Course team data
* Discussion data
* Certificates

To export a course:
 
#. From the **Tools** menu, select **Export**.
#. Click **Export Course Content**.

When the export completes you can then access the .tar.gz file on your computer.


.. _Import a Course:

*************** 
Import a Course
***************

.. warning::

	Content of the imported course replaces all the content of this course.
	**You cannot undo a course import**. We recommend that you first export the
	current course, so you have a backup copy of it.
 
There are several reasons you may want to import a course:

* To run a new version of an existing course
* To replace an existing course 
* To load a course you developed outside of Studio


The course that you import must be in a .tar.gz file (that is, a .tar file
compressed with GNU Zip). This .tar.gz file must contain a course.xml file in a
course data directory. The tar.gz file must have the same name as the course
data directory. It may also contain other files.
 
If your course uses legacy layout structures, you may not be able to edit the
course in Studio, although it will probably appear correctly on Edge. To make
sure that your course is completely editable, ensure that all of your material
is embedded in a unit.
 
The import process has five stages. During the first two stages, you must stay
on the Course Import page. You can leave this page after the Unpacking stage has
completed. We recommend, however, that you don't make important changes to your
course until the import operation has completed.
 
To import a course:
 
#. From the **Tools** menu, select **Import**.
#. Click **Choose a File to Import**.
#. Locate the file that you want, and then click **Open**.
#. Click **Replace my course with the one above**.

