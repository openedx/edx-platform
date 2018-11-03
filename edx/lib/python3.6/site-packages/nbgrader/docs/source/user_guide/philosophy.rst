
The philosophy and the approach
===============================

The `nbgrader` project evolved from my experiences as an instructor and a
student. This `excerpt from David Marr's book <https://www.dropbox.com/s/olrx40rzzvk1v1i/Marr%20-%20The%20Philosophy%20and%20the%20Approach.pdf?dl=0>`_, *Vision*,
is one of the core readings of the class that inspired the creation of
`nbgrader`. Dr. Marr was an originator of the field of computational
neuroscience and has been extremely influential in the field of computational cognitive science as well. On behalf of the many individuals who contribute to `nbgrader`, I hope you find this project enhances your teaching and learning experiences.

-- *Jess Hamrick*, UC Berkeley


How to structure course files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For instructor ease of use and developer maintenance, nbgrader makes a few
assumptions about how your assignment files are organized. By default,
nbgrader assumes that your assignments will be organized with the following
directory structure:

::

    {course_directory}/{nbgrader_step}/{student_id}/{assignment_id}/{notebook_id}.ipynb
    
where:

* ``course_directory`` variable is the root directory where you run the
  nbgrader commands. This means that you can place your class files directory
  wherever you want. However, this location can also be customized (see the
  :doc:`configuration options </configuration/config_options>`) so that you can run the
  nbgrader commands from anywhere on your system, but still have them
  operate on the same directory.
  
* ``nbgrader_step`` - Each subcommand of nbgrader (e.g. ``assign``,
  ``autograde``, etc.) has different input and output folders associated with
  it. These correspond to the ``nbgrader_step`` variable -- for example, the
  default input step directory for ``nbgrader autograde`` is "submitted",
  while the default output step directory is "autograded".

* ``student_id`` corresponds to the unique ID of a student.

* ``assignment_id`` corresponds to the unique name of an assignment.

* ``notebook_id`` corresponds to the name of a notebook within an assignment
  (excluding the .ipynb extension).

Example
-------
Taking the autograde step as an example, when we run the command
``nbgrader autograde "Problem Set 1"``, nbgrader will look for all
notebooks that match the following path:

::

    submitted/*/Problem Set 1/*.ipynb

For each notebook that it finds, it will extract the ``student_id``,
``assignment_id``, and ``notebook_id`` according to the directory
structure described above. It will then autograde the notebook, and save
the autograded version to:

::

    autograded/{student_id}/Problem Set 1/{notebook_id}.ipynb

where ``student_id`` and ``notebook_id`` were parsed from the input file
path.

Here is how a sample directory structure for the course named
``course101`` might look, where the users ``bitdiddle`` and ``hacker``
have submitted solutions to the assignment ``ps1``:

::

   course101/
   ├── gradebook.db
   ├── nbgrader_config.py
   ├── source
   │   ├── header.ipynb
   │   └── ps1
   │       ├── jupyter.png
   │       ├── problem1.ipynb
   │       └── problem2.ipynb
   ├── release
   │   └── ps1
   │       ├── jupyter.png
   │       ├── problem1.ipynb
   │       └── problem2.ipynb
   ├── submitted
   │   ├── bitdiddle
   │   │   └── ps1
   │   │       ├── jupyter.png
   │   │       ├── problem1.ipynb
   │   │       ├── problem2.ipynb
   │   │       └── timestamp.txt
   │   └── hacker
   │       └── ps1
   │           ├── jupyter.png
   │           ├── problem1.ipynb
   │           ├── problem2.ipynb
   │           └── timestamp.txt
   ├── autograded/
   └── feedback/

Database of assignments
~~~~~~~~~~~~~~~~~~~~~~~

Additionally, nbgrader needs access to a database to store information about
the assignments. This database is, by default, a sqlite database that lives at
``{course_directory}/gradebook.db``, but you can also configure this to be any
location of your choosing. You do not need to manually create this database
yourself, as nbgrader will create it for you, but you probably want to
prepopulate it with some information about assignment due dates and students
(see :doc:`managing_the_database`).

Additionally, nbgrader uses SQLAlchemy, so you should be able to also use MySQL
or PostgreSQL backends as well (though in these cases, you *will* need to
create the database ahead of time, as this is just how MySQL and PostgreSQL
work).

Configuration files
~~~~~~~~~~~~~~~~~~~

To customize nbgrader's behavior, you can set configuration options in the
``nbgrader_config.py`` file. In particular, if you are using nbgrader with
:doc:`JupyterHub </configuration/jupyterhub_config>`, you must set the
course id in the nbgrader configuration file. A basic nbgrader config file
would live at ``{course_directory}/nbgrader_config.py`` and might look like:

::

    c = get_config()
    c.Exchange.course_id = "course101"

There are many additional options you can configure. See :doc:`/configuration/config_options` for a full list.
