
Installation
============

The nbgrader system and command line tools
------------------------------------------
You may install the current version of nbgrader which includes the grading
system and command line tools::

    pip install nbgrader

Or, if you use `Anaconda <https://www.continuum.io/downloads>`__::

    conda install jupyter
    conda install -c conda-forge nbgrader

nbgrader extensions
-------------------

**Take note:** If you install nbgrader via `Anaconda
<https://www.continuum.io/downloads>`__ the nbgrader extensions will be
installed and enabled for you upon installation. See the `Installation
options`_ and `Disabling extensions`_ sections below for more information on
changing the default installation option ``--sys-prefix`` or disabling one or
more extensions.

Installing and activating extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can install the nbgrader extensions for Jupyter notebook. Previously
this was done using the ``nbgrader extension install`` command. However, moving
forward this is done using the ``jupyter nbextension`` and ``jupyter
serverextension`` commands.

To install and enable all nbextensions (**assignment list**, **create
assignment**, **formgrader**, and **validate**) run::

    jupyter nbextension install --sys-prefix --py nbgrader --overwrite
    jupyter nbextension enable --sys-prefix --py nbgrader
    jupyter serverextension enable --sys-prefix --py nbgrader

To work properly, the **assignment list**, **formgrader**, and **validate**
extensions require both the nbextension and serverextension. The **create
assignment** extension only has an nbextension part.

Installation options
~~~~~~~~~~~~~~~~~~~~

When installed/enabled with the ``--sys-prefix`` option, the nbextensions and
serverextension will be installed and enabled for anyone using the particular
Python installation or conda environment where nbgrader is installed. If that
Python installation is available system-wide, all users will immediately be
able to use the nbgrader extensions.

There are a number of ways you may need to customize the installation:

-  To install or enable the nbextensions/serverextension for just the
   current user, replace ``--sys-prefix`` by ``--user`` in any of the above
   commands.

-  To install or enable the nbextensions/serverextension for all
   Python installations on the system, replace ``--sys-prefix`` by ``--system``
   in any of the above commands.

-  You can also use the ``--overwrite`` option along with the ``jupyter
   nbextension install`` command to overwrite existing nbgrader extension
   installation files, typically used when updating nbgrader, for
   example::

    jupyter nbextension install --sys-prefix --overwrite --py nbgrader

Previous versions of nbgrader required each user on a system to enable the
nbextensions; this is no longer needed if the ``--sys-prefix`` option is used
for a system-wide python or the ``--system`` option is used.

Disabling extensions
~~~~~~~~~~~~~~~~~~~~

You may want to only install one of the nbgrader extensions. To do this, follow
the above steps to install everything and then disable the extension you don't
need. For example, to disable the Assignment List extension:

    jupyter nbextension disable --sys-prefix assignment_list/main --section=tree
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list

or to disable the Create Assignment extension::

    jupyter nbextension disable --sys-prefix create_assignment/main

or to disable the Formgrader extension::

    jupyter nbextension disable --sys-prefix formgrader/main --section=tree
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader

For example lets assume you have installed nbgrader via `Anaconda
<https://www.continuum.io/downloads>`__ (meaning all extensions are installed
and enabled with the ``--sys-prefix`` flag, i.e. anyone using the particular
Python installation or conda environment where nbgrader is installed). But you
only want the *create assignment* extension available to a specific user and
not everyone else. First you will need to disable the *create assignment*
extension for everyone else::

    jupyter nbextension disable --sys-prefix create_assignment/main

Log in with the specific user and then enable the *create assignment* extension
only for that user::

    jupyter nbextension enable --user create_assignment/main

Finally to see all installed nbextensions/server extensions, run::

    jupyter nbextension list
    jupyter serverextension list

For further documentation on these commands run::

    jupyter nbextension --help-all
    jupyter serverextension --help-all

For advanced instructions on installing the *assignment list* extension please
see the :ref:`advanced installation instructions<assignment-list-installation>`.

Quick start
-----------

To get up and running with nbgrader quickly, you can create an example
directory with example course files in it by running the ``nbgrader
quickstart`` command::

    nbgrader quickstart course_id

Where you should replace ``course_id`` with the name of your course. For
further details on how the quickstart command works, please run:

    nbgrader quickstart --help

For an explanation of how this directory is arranged, and what the different
files are in it, continue reading on in :doc:`philosophy`.
