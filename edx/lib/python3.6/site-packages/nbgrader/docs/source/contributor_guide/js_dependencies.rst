JavaScript dependencies
=======================

For the time being, we are committing JavaScript dependencies to the nbgrader
repository as that makes nbgrader installation much easier.

Adding or updating JavaScript libraries
---------------------------------------
If you need to add a new library, or update the version of a library, you will
need to have `npm` installed.

To install npm on OS X, use Homebrew to install node (npm will be installed
along with node)::

    brew update
    brew install node

To install npm on Linux with apt-get, use::

    apt-get update
    apt-get install node
    apt-get install npm

Modify the ``bower.json`` file in the root of the nbgrader
repository and then run::

    invoke js

This will download and install the correct versions of the dependencies to
``nbgrader/server_extensions/formgrader/static/components``.
Usually, JavaScript libraries installed in this way include a lot of extra files
(e.g. tests, documentation) that we don't want to commit to the nbgrader
repository. If this is the case, please add these files to the
``.gitignore`` file so these extra files are ignored and don't get
committed.
