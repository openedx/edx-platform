*******************************************
Paver
*******************************************


Paver provides a standardised way of managing development and operational tasks in edX.

To run individual commands, use the following syntax:

paver <command_name> --option=<option value>


Paver Commands
*******************************************

Paver commands are grouped as follows:

- Prereqs_ Install all of the prerequisite environments for Python, Node and Ruby
- Docs_ Docs is used to build and then optionally display the EdX docs relating to development, authoring and data management
- Assets_ Assets will compile Sass (CSS), Coffeescript (Javascript) and XModule assets. Optionally it can call Django’s collectstatic method
- `Run Servers`_ Run servers


.. _Prereqs:

Prereqs
=============

Install all of the prerequisite for Python, Node and Ruby

   **install_prereqs** : installs Ruby, Node and Python requirements

::

   paver install_prereqs

..


.. _Docs:

Docs
=============

Docs is used to build and then optionally display the EdX docs relating to development, authoring and data management

   **build_docs**:  Invoke sphinx 'make build' to generate docs.

    *--type=* <dev, author, data> Type of docs to compile

    *--verbose* Display verbose output

::

   paver build_docs --type=dev --verbose

..


.. _Assets:

Assets
=============

Assets will compile Sass (CSS), CoffeeScript (Javascript) and XModule assets. Optionally it can call Django's collectstatic command.


   **update_assets**: Compiles Coffeescript, Sass, Xmodule and runs collectstatic

    *system* lms or studio

    *--settings=* Django settings e.g. aws, dev, devstack (the default)

    *--debug* Disable Sass compression

    *--skip-collect* Skip collection of static assets

::

   paver update_assets lms

..

.. _Run Servers:

Run Servers
=============

    **lms**: runs LMS server

     *--settings=* Django settings e.g. aws, dev, devstack (the default)

     *--fast*   Skip updating assets

::

   paver lms --settings=dev

..


    **studio**: runs Studio

     *--settings=* Django settings e.g. aws, dev, devstack (the default)

     *--fast*   Skip updating assets

::

   paver studio --settings=dev

..


    **run_all_servers**: runs lms, cms and celery workers

     *--settings=* Django settings e.g. aws, dev, devstack (the default)

     *--worker_settings=* Django settings for celery workers


::

   paver run_all_servers --settings=dev --worker_settings=celery

..


    **run_celery**: runs celery for specified system

     *--settings=* Environment settings e.g. aws, dev both for LMS and Studio

     *--settings_lms=* Override django settings for LMS e.g. lms.dev

     *--settings_cms=* Override django settings for Studio


::

   paver celery --settings=dev

..

    **update_db**: runs syncdb and then migrate

     *--settings=* Django settings e.g. aws, dev, devstack (the default)

::

   paver update_db --settings=dev

..


    **check_settings**: checks settings files

     *system*: System to check (lms or studio)
     *settings*: Django settings to check.

::

   paver check_settings lms aws

..

