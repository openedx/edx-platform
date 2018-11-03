Developer installation
======================

Getting the source code
-----------------------
The source files for nbgrader and its documentation are hosted on GitHub. To
clone the nbgrader repository::

    git clone https://github.com/jupyter/nbgrader
    cd nbgrader

Installing and building nbgrader
-------------------------------------
nbgrader installs and builds with one command::

    pip install -r dev-requirements.txt -e .

Currently, building docs is not supported on Windows because some of the dependencies (enchant)
are not easily installable. Instead of the above command, run the following on windows::

    pip install -r dev-requirements-windows.txt -e .


Installing notebook extensions
------------------------------
Previously this was done using the ``nbgrader extension install`` command.
However, moving forward this is done using the ``jupyter nbextension`` and
``jupyter serverextension`` commands.

To install and enable all the frontend nbextensions (*assignment list*,
*create assignment*, and *formgrader*) run::

    # The nbextensions are JavaScript/HTML/CSS so they require
    # separate installation and enabling.
    jupyter nbextension install --symlink --sys-prefix --py nbgrader
    jupyter nbextension enable --sys-prefix --py nbgrader

The ``--symlink`` option is recommended since it updates the extensions
whenever you update the nbgrader repository. To install the server extensions
for *assignment_list* and *formgrader* run::

    # The serverextension is a Python module inside nbgrader, so only an
    # enable step is needed.
    jupyter serverextension enable --sys-prefix --py nbgrader

To work properly, the *assignment list* and *formgrader* extensions require
both the nbextension and serverextension. The *create assignment* extension
only has an nbextension part.

Installing Phantomjs
--------------------
To run tests while developing nbgrader and its documentation, Phantomjs must
be installed.

Install using npm
~~~~~~~~~~~~~~~~~
If you have npm installed, you can install phantomjs using::

    npm install phantomjs

Install using other package managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you do not have npm installed, you can still install phantomjs.

On OS X::

    brew update
    brew install phantomjs

On Linux::

    apt-get update
    apt-get install phantomjs
