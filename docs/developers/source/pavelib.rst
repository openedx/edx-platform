*******************************************
Paver
*******************************************


Paver provides a standardised way of managing development and operational tasks in edX.

To run individual commands, use the following syntax:

paver <command_name> --option=<option value>


Paver Commands
*******************************************

Paver commands are grouped as follows:

- Prereqs_ Install all of the prerequisite environments for python, node and ruby
- Docs_ Docs is used to build and then optionally display the edX docs relating to development, authoring and data management
- Assets_ Assets will compile sass (css), coffeescript (javascript) and xmodule assets. Optionally it can call django’s collectstatic method
- `Run Servers`_ Run servers
- `Developer Stack`_ Management of developer vagrant environment
- Translation_ Tasks for dev internationalisation support
- `Bok Choy Testing`_ Run acceptance tests that use the bok-choy framework http://bok-choy.readthedocs.org/en/latest/
- `Acceptance Test`_ Run acceptance tests
- `Javascript Test`_ Run Javascript tests
- Quality_ Run lint, pep8 and coverage tools
- Tests_ Run all tests
- Workspace_ Migration utilities


.. _Prereqs:

Prereqs
=============

Install all of the prerequisite environments for python, node and ruby

   **install_prereqs** : installs ruby, node and python

::

   paver install_prereqs

..

Runs following commands:

   **install_ruby_prereqs** : Installs ruby prereqs. Reguires bundler

::

   paver install_ruby_prereqs

..

   **install_node_prereqs**: Installs Node prereqs. Requires npm

::

   paver install_node_prereqs

..

   **install_python_prereqs**: Installs Python prereqs. Requires pip

::

   paver install_python_prereqs

..


.. _Docs:

Docs
=============

Docs is used to build and then optionally display the edX docs relating to development, authoring and data management

   **build_docs**:  Invoke sphinx 'make build' to generate docs.

    **--type=** <dev, author, data> Type of docs to compile

    **--verbose** Display verbose output

::

   paver build_docs --type=dev --verbose

..

   **show_docs**: Show docs in browser

    *--type=* <dev, author, data> Type of docs to compile

::

   paver show_docs --type=dev

..

   **doc**:  Invoke sphinx 'make build' to generate docs and then show in browser

    *--type=* <dev, author, data> Type of docs to compile

    *--verbose* Display verbose output

::

   paver doc --type=dev --verbose

..


.. _Assets:

Assets
=============

Assets will compile sass (css), coffeescript (javascript) and xmodule assets. Optionally it can call django's
collectstatic method

   **pre_django**:  Installs requirements and cleans previous python compiled files

::

   paver pre_django

..


   **compile_coffeescript**: Compiles Coffeescript files

    *--system=*   System to act on e.g. lms, cms

    *--env=*      Environment settings e.g. aws, dev

    *--watch*     Run with watch

    *--debug*     Run with debug

    *--clobber*   Remove compiled Coffeescript files

::

   paver compile_coffeescript --system=lms --env=dev --watch --debug

..

   **compile_sass**: Compiles Sass files

    *--system=* System to act on e.g. lms, cms

    *--env=* Environment settings e.g. aws, dev

    *--watch* Run with watch

    *--debug* Run with debug

::

   paver compile_sass --system=lms --env=dev --watch --debug

..

   **compile_xmodule**: Compiles Xmodule

    *--system=* System to act on e.g. lms, cms

    *--env=* Environment settings e.g. aws, dev

    *--watch* Run with watch

    *--debug* Run with debug

::

   paver compile_xmodule --system=lms --env=dev --watch --debug

..


   **compile_assets**: Compiles Coffeescript, Sass, Xmodule and optionally runs collectstatic

    *--system=* System to act on e.g. lms, cms

    *--env=* Environment settings e.g. aws, dev

    *--watch* Run with watch

    *--debug* Run with debug

    *--collectstatic* Runs collectstatic

::

   paver compile_sass --system=lms --env=dev --watch --debug

..

.. _Run Servers:

Run Servers
=============

    **lms**: runs lms

     *--env=* Environment settings e.g. aws, dev

::

   paver lms --env=dev

..


    **cms**: runs cms

     *--env=* Environment settings e.g. aws, dev

::

   paver cms --env=dev

..

    **run_server**: run a specific server

     *--system=* System to act on e.g. lms, cms

     *--env=* Environment settings e.g. aws, dev

::

   paver run_server --system=lms --env=dev

..

    **resetdb**: runs syncdb and then migrate

     *--env=* Environment settings e.g. aws, dev

::

   paver resetdb --env=dev

..


    **check_settings**: checks settings files

     *--env=* Environment settings e.g. aws, dev

::

   paver check_settings --env=dev

..


    **run_all_servers**: runs lms, cms and celery workers

     *--env=* Environment settings e.g. aws, dev

     *--worker_env=* Environment settings for celery workers

     *--logfile=* File to log output to

::

   paver run_all_servers --env=dev --worker_env=celery --logfile=log.txt

..


    **run_celery**: runs celery for specified system

     *--system=* System to act on e.g. lms, cms

     *--env=* Environment settings e.g. aws, dev

::

   paver run_celery --system=lms --env=dev

..

.. _Developer Stack:

Developer Stack
===============

Management of developer vagrant environment




    **devstack_assets**: Update static assets

     *--system=*   System to act on e.g. lms, cms

::

   paver devstack_assets --system=lms

..


    **devstack_start**: Start the server specified

     *--system=*   System to act on e.g. lms, cms

::

   paver devstack_start --system=lms

..



    **devstack_install**: Update Python, Ruby, and Node requirements

::

   paver devstack_install

..


    **devstack**: Install prerequisites, compile assets and run the system specified

     *--system=*   System to act on e.g. lms, cms

::

   paver devstack --system=lms

..


.. _Translation:

Translation
=============

Tasks for dev internationalisation support

    **i18n_extract**: Extract localizable strings from sources

::

   paver i18n_extract

..


   **i18n_validate_gettext**: Make sure GNU gettext utilities are available

::

   paver i18n_validate_gettext

..


   **i18n_generate**: Compile localizable strings from sources. With optional flag 'extract', will extract strings first.

    *--extract* Extract first

::

   paver i18n_generate --extract

..



   **i18n_dummy**: Simulate international translation by generating dummy strings corresponding to source strings.

::

   paver i18n_dummy

..



   **i18n_validate_transifex_config**: Make sure config file with username/password exists

::

   paver i18n_validate_transifex_config

..


   **i18n_transifex_push**: Push source strings to Transifex for translation

::

   paver i18n_transifex_push

..


   **i18n_transifex_pull**: Pull source strings from Transifex

::

   paver i18n_transifex_pull

..


   **i18n_transifex_test**: Test translation

::

   paver i18n_transifex_test

..


.. _Bok Choy Testing:

Bok Choy Testing
================

Run acceptance tests that use the bok-choy framework http://bok-choy.readthedocs.org/en/latest/



    **bok_choy_setup**: Process assets and set up database for bok-choy tests

     *--system=*   System to act on e.g. lms, cms

::

   paver bok_choy_setup --system=lms

..


    **test_bok_choy_fast**: Run acceptance tests that use the bok-choy framework but skip setup

     *--test_spec=*   Test specification

::

   paver test_bok_choy_fast --test_spec=specification

..


    **test_bok_choy**: Run acceptance tests that use the bok-choy framewor

     *--test_spec=*   Test specification

::

   paver test_bok_choy --test_spec=specification

..


.. _Acceptance Test:

Acceptance Test
================

Run acceptance tests

    **test_acceptance_all**: Run acceptance tests on all systems

     *--system=*   System to act on e.g. lms, cms

     *--harvest_args=*   Arguments to pass to the harvest command

::

   paver test_acceptance_all --harvest_args=<harvest args>

..



    **test_acceptance**: Run acceptance tests on system specified

     *--system=*   System to act on e.g. lms, cms

     *--harvest_args=*   Arguments to pass to the harvest command

::

   paver test_acceptance --system=lms --harvest_args=<harvest args>

..



    **test_acceptance_fast**: Run acceptance tests withouth collectstatic and without init db

     *--system=*   System to act on e.g. lms, cms

     *--harvest_args=*   Arguments to pass to the harvest command

::

   paver test_acceptance_fast --system=lms --harvest_args=<harvest args>

..

.. _Javascript Test:

Javascript Test
================

Run javascript tests. This mainly uses the js-test-tool

    **test_js_run**: Run the JavaScript tests and print results to the console

     *--suite=*   Test suite to run

::

   paver test_js_run --suite=lms

..

    **test_js**: Run the JavaScript tests and print results to the console

     *--suite=*   Test suite to run

::

   paver test_js --suite=lms

..

    **test_js_dev**: Run the JavaScript tests in your default browser

     *--suite=*   Test suite to run

::

   paver test_js_dev --suite=lms

..

    **test_js_coverage**: Run all JavaScript tests and collect coverage information

::

   paver test_js_coverage

..

    **test_js**: Run all JavaScript tests and collect coverage information

::

   paver test_js

..

.. _Quality:

Quality
=======

Run lint and coverage tools


    **run_pylint**: Run pylint checking for {system} if --errors specified check for errors only, and abort if there are any

     *--system=* System to act on e.g. lms, cms

     *--errors* Check for errors only

::

   paver run_pylint --system=lms --errors

..



    **run_pep8**: Run pep8 on system code

     *--system=* System to act on e.g. lms, cms

::

   paver run_pep8 --system=lms

..


    **run_quality**: Build the html diff quality reports, and print the reports to the console.

     *--system=* System to act on e.g. lms, cms

::

   paver run_quality --system=lms

..


.. _Tests:

Tests
=======

Runs tests


    **test_docs**: Run documentation tests

::

   paver test_docs

..


    **clean_test_files**: Clean fixture files used by tests and .pyc files

::

   paver clean_test_files

..


    **clean_reports_dir**: Clean coverage files, to ensure that we don't use stale data to generate reports.

::

   paver clean_reports_dir

..

    **test_system**: Run all django tests on our djangoapps for system

     *--system=* System to act on e.g. lms, cms

::

   paver test_system --system=lms

..


    **fasttest**: Run the tests without running collectstatic

     *--system=* System to act on e.g. lms, cms

     *--test_id=* Provide a test id

::

   paver fasttest --system=lms --test_id=id

..



    **test_lib**: Run tests for common lib

     *--lib=* lib to test

::

   paver test_lib --lib=

..



    **fasttest_lib**: Run tests for common lib (aliased for backwards compatibility).  Run all django tests on our djangoapps for system

     *--lib=* lib to test


::

   paver fasttest_lib --lib=

..



    **test_python**: Run all python tests

::

   paver test_python

..

    **test**: Run all tests

::

   paver test

..

    **coverage**: Build the html, xml, and diff coverage reports

::

   paver coverage

..


.. _Workspace:

Workspace
=========

Migration tool to run arbitrary scripts


    **workspace_migrate**: Run scripts in ws_migrations directory

::

   paver workspace_migrate

..


