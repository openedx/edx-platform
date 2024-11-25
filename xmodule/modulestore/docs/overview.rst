<<<<<<< HEAD
#################################
Overview of the edX Modulestores
#################################
=======
################################
Overview of the edX Modulestores
################################
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

The edX Platform uses several different modulestores to store course data. Each
of these modulestores is in use on edx.org.

See:

* `XMLModuleStore`_
* `DraftModuleStore`_
* :ref:`Split Mongo Modulestore`

<<<<<<< HEAD
***************
XMLModuleStore
***************
=======
**************
XMLModuleStore
**************
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

The XMLModuleStore was the first modulestore used for the edX Platform.

XMLModuleStore uses a file system that stores XML-based courses.  When the LMS
server starts, XMLModuleStore loads every block for every course into memory.

XMLModuleStore is read-only and does not enable users to change a course
without restarting the server.

<<<<<<< HEAD
*****************
DraftModuleStore
*****************
=======
****************
DraftModuleStore
****************
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

DraftModuleStore was the next generation modulestore and provides greater
scalability by allowing random access to course blocks and loading blocks on
requests.

DraftModuleStore allows editing of courses without restarting the server.

In addition, DraftModuleStore stores a draft version of some types of blocks.

<<<<<<< HEAD
*****************
Split Mongo
*****************
=======
***********
Split Mongo
***********
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

Split Mongo is the newest modulestore.  See the :ref:`Split Mongo Modulestore`
chapter for more information.