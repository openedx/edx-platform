#######
Testing
#######

.. contents::
   :local:
   :depth: 3

Overview
========

We maintain two kinds of tests: unit tests and integration tests.

Overall, you want to write the tests that **maximize coverage** while
**minimizing maintenance**. In practice, this usually means investing
heavily in unit tests, which tend to be the most robust to changes in
the code base.

.. figure:: test_pyramid.png
   :alt: Test Pyramid

   Test Pyramid

The pyramid above shows the relative number of unit tests and integration
tests. Most of our tests are unit tests or
integration tests.

Test Types
----------

Unit Tests
~~~~~~~~~~

-  Each test case should be concise: setup, execute, check, and
   teardown. If you find yourself writing tests with many steps,
   consider refactoring the unit under tests into smaller units, and
   then testing those individually.

-  As a rule of thumb, your unit tests should cover every code branch.

-  Mock or patch external dependencies. We use the voidspace `Mock Library`_.

-  We unit test Python code (using `unittest`_) and Javascript (using
   `Jasmine`_)

.. _Mock Library: http://www.voidspace.org.uk/python/mock/
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _Jasmine: http://jasmine.github.io/


Integration Tests
~~~~~~~~~~~~~~~~~

-  Test several units at the same time. Note that you can still mock or patch
   dependencies that are not under test! For example, you might test that
   ``LoncapaProblem``, ``NumericalResponse``, and ``CorrectMap`` in the ``capa``
   package work together, while still mocking out template rendering.

-  Use integration tests to ensure that units are hooked up correctly.  You do
   not need to test every possible input--that's what unit tests are for.
   Instead, focus on testing the "happy path" to verify that the components work
   together correctly.

-  Many of our tests use the `Django test client`_ to simulate HTTP requests to
   the server.

.. _Django test client: https://docs.djangoproject.com/en/dev/topics/testing/overview/

Test Locations
--------------

-  Python unit and integration tests: Located in subpackages called
   ``tests``. For example, the tests for the ``capa`` package are
   located in ``xmodule/capa/tests``.

-  Javascript unit tests: Located in ``spec`` folders. For example,
   ``xmodule/js/spec`` and
   ``{cms,lms}/static/js/spec`` For consistency, you should use the
   same directory structure for implementation and test. For example,
   the test for ``src/views/module.js`` should be written in
   ``spec/views/module_spec.js``.

Running Tests
=============

You can run all of the unit-level tests using this command::

    paver test

This includes python, JavaScript, and documentation tests.

Note -
`paver` is a scripting tool. To get information about various options, you can run the this command::

    paver -h

Note -
Unless otherwise mentioned, all the following commands should be run from inside lms docker container.

Running Python Unit tests
-------------------------

We use `pytest`_ to run Python tests. Pytest is a testing framework for python and should be your goto for local Python unit testing.

Pytest (and all of the plugins we use with it) has a lot of options. Use `pytest --help` to see all your option and pytest has good docs around testing.

.. _pytest: https://pytest.org/


Running a Single Test
~~~~~~~~~~~~~~~~~~~~~

When developing tests, it is often helpful to be able to really just run one single test without the overhead of PIP installs, UX builds, etc.

Various ways to run tests using pytest::

    pytest path/test_m­odule.py                          # Run all tests in a module.
    pytest path/test_m­odule.p­y:­:te­st_func               # Run a specific test within a module.
    pytest path/test_m­odule.p­y:­:Te­stC­las­s               # Run all tests in a class
    pytest path/test_m­odule.p­y:­:Te­stC­las­s::­tes­t_m­ethod  # Run a specific method of a class.
    pytest path/testing/                                # Run all tests in a directory.

For example, this command runs a single python unit test file::

    pytest xmodule/tests/test_stringify.py

Note -
edx-platorm has multiple services (lms, cms) in it. The environment for each service is different enough that we run some tests in both environments in jenkins. To make sure tests will pass in each of these environments (especially for tests in "common" directory), you will need to test in each seperately. Add --rootdir flag at end of your pytest call and specify the env you are testing in::

    pytest test --rootdir <lms or cms>

Various tools like ddt create tests with very complex names, rather than figuring out the name yourself, you can:

1. Select tests to run based on their name, provide an expression to the `pytest -k option`_ which performs a substring match on test names::

    pytest xmodule/tests/test_stringify.py -k test_stringify

.. _pytest -k option: https://docs.pytest.org/en/latest/example/markers.html#using-k-expr-to-select-tests-based-on-their-name
.. _node ID: https://docs.pytest.org/en/latest/example/markers.html#node-id


2. Alternatively, you can the get the name of all test methods in a class, file, or project, including all ddt.data variations, by running pytest with `--collectonly`::

    pytest xmodule/tests/test_stringify.py --collectonly

Testing with migrations
***********************

For the sake of speed, by default the python unit test database tables
are created directly from apps' models. If you want to run the tests
against a database created by applying the migrations instead, use the
``--create-db --migrations`` option::

    pytest test --create-db --migrations

Debugging a test
~~~~~~~~~~~~~~~~

There are various ways to debug tests in Python and more specifically with pytest:

- using the verbose -v or really verbose -vv flags can be helpful for displaying diffs on assertion failures

- if you want to focus on one test failure at a time, the ``--exitfirst``or ``-x`` flags to have pytest stop after the first failure

- by default, the plugin pytest-randomly will randomize test case sequence. This is to help reveal bugs in your test setup and teardown. If you do not want this randomness, use the --randomly-dont-reorganize flag

- if you pass the ``--pdb`` flag to a pytest call, the test runner will drop you into pdb on error. This lets you go up and down the stack and see what the values of the variables are. Check out `the pdb documentation`_.  Note that this only works if you aren't collecting coverage statistics (pdb and coverage.py use the same mechanism to trace code execution).

- If there is a specific point in code you would like to debug, you can add the build-in "breakpoint()" function there and it will automatically drop you at the point next time the code runs. If you check this in, your tests will hang on jenkins. Example of use::

    if True:
      # you will be dropped here in the pdb shell when running test or code
      breakpoint()
      a=2
      random_variable = False

.. _the pdb documentation: http://docs.python.org/library/pdb.html


How to output coverage locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are examples of how to run a single test and get coverage::

    pytest cms/djangoapps/contentstore/tests/test_import.py --cov --cov-config=.coveragerc-local # cms example
    pytest lms/djangoapps/courseware/tests/test_module_render.py --cov --cov-config=.coveragerc-local # lms example

That ``--cov-conifg=.coveragerc-local`` option is important - without it, the coverage
tool will look for paths that exist on our jenkins test servers, but not on your local devstack.

How to spit out coverage for a single file with a list of each line that is missing coverage::

   pytest lms/djangoapps/grades/tests/test_subsection_grade.py \
       --cov=lms.djangoapps.grades.subsection_grade \
       --cov-config=.coveragerc-local \
       --cov-report=term-missing
   ---------- coverage: platform linux2, python 2.7.12-final-0 ----------

   Name                                        Stmts   Miss  Cover   Missing
   -------------------------------------------------------------------------
   lms/djangoapps/grades/subsection_grade.py     125     38    70%   47-51, 57, 80-81, 85, 89, 99, 109, 113, [...]

Use this command to generate a coverage report (after previously running ``pytest``)::

    coverage report

The above command looks for a test coverage data file in ``reports/.coverage`` - this file will
contain coverage data from your last run of ``pytest``.  Coverage data is recorded for whichever
paths you specified in your ``--cov`` option, e.g.::

    --cov=.  # will track coverage for the entire project
    --cov=path.to.your.module  # will track coverage only for "module"

Use this command to generate an HTML report::

    coverage html

The report is then saved in reports/xmodule/cover/index.html

To run tests for stub servers, for example for `YouTube stub server`_, you can
run one of these commands::

    paver test_system -s cms -t common/djangoapps/terrain/stubs/tests/test_youtube_stub.py
    pytest common/djangoapps/terrain/stubs/tests/test_youtube_stub.py

.. _YouTube stub server: https://github.com/openedx/edx-platform/blob/master/common/djangoapps/terrain/stubs/tests/test_youtube_stub.py


Debugging Unittest Flakiness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we move over to running our unittests with Jenkins Pipelines and pytest-xdist,
there are new ways for tests to flake, which can sometimes be difficult to debug.
If you run into flakiness, check (and feel free to contribute to) this
`confluence document <https://openedx.atlassian.net/wiki/spaces/TE/pages/884998163/Debugging+test+failures+with+pytest-xdist>`__ for help.

Running Javascript Unit Tests
-----------------------------

We use Jasmine to run JavaScript unit tests. To run all the JavaScript
tests::

    paver test_js

To run a specific set of JavaScript tests and print the results to the
console, run these commands::

    paver test_js_run -s lms
    paver test_js_run -s cms
    paver test_js_run -s cms-squire
    paver test_js_run -s xmodule
    paver test_js_run -s xmodule-webpack
    paver test_js_run -s common
    paver test_js_run -s common-requirejs

To run JavaScript tests in a browser, run these commands::

    paver test_js_dev -s lms
    paver test_js_dev -s cms
    paver test_js_dev -s cms-squire
    paver test_js_dev -s xmodule
    paver test_js_dev -s xmodule-webpack
    paver test_js_dev -s common
    paver test_js_dev -s common-requirejs

Debugging Specific Javascript Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to debug individual tests is to run the test suite in the browser and
use your browser's Javascript debugger. The debug page will allow you to select
an individual test and only view the results of that test.


Debugging Tests in a Browser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug these tests on devstack in a local browser:

* first run the appropriate test_js_dev command from above
* open http://localhost:19876/debug.html in your host system's browser of choice
* this will run all the tests and show you the results including details of any failures
* you can click on an individually failing test and/or suite to re-run it by itself
* you can now use the browser's developer tools to debug as you would any other JavaScript code

Note: the port is also output to the console that you ran the tests from if you find that easier.

These paver commands call through to Karma. For more
info, see `karma-runner.github.io <https://karma-runner.github.io/>`__.

Testing internationalization with dummy translations
----------------------------------------------------

Any text you add to the platform should be internationalized. To generate translations for your new strings, run the following command::

    paver i18n_dummy

This command generates dummy translations for each dummy language in the
platform and puts the dummy strings in the appropriate language files.
You can then preview the dummy languages on your local machine and also in your sandbox, if and when you create one.

The dummy language files that are generated during this process can be
found in the following locations::

    conf/locale/{LANG_CODE}

There are a few JavaScript files that are generated from this process. You can find those in the following locations::

    lms/static/js/i18n/{LANG_CODE}
    cms/static/js/i18n/{LANG_CODE}

Do not commit the ``.po``, ``.mo``, ``.js`` files that are generated
in the above locations during the dummy translation process!

Test Coverage and Quality
-------------------------

Viewing Test Coverage
~~~~~~~~~~~~~~~~~~~~~

We currently collect test coverage information for Python
unit/integration tests.

To view test coverage:

1. Run the test suite with this command::

       paver test

2. Generate reports with this command::

       paver coverage

3. Reports are located in the ``reports`` folder. The command generates
   HTML and XML (Cobertura format) reports.

Python Code Style Quality
~~~~~~~~~~~~~~~~~~~~~~~~~

To view Python code style quality (including PEP 8 and pylint violations) run this command::

    paver run_quality

More specific options are below.

-  These commands run a particular quality report::

       paver run_pep8
       paver run_pylint

-  This command runs a report, and sets it to fail if it exceeds a given number
   of violations::

       paver run_pep8 --limit=800

-  The ``run_quality`` uses the underlying diff-quality tool (which is packaged
   with `diff-cover`_). With that, the command can be set to fail if a certain
   diff threshold is not met. For example, to cause the process to fail if
   quality expectations are less than 100% when compared to master (or in other
   words, if style quality is worse than what is already on master)::

       paver run_quality --percentage=100

-  Note that 'fixme' violations are not counted with run\_quality. To
   see all 'TODO' lines, use this command::

       paver find_fixme --system=lms

   ``system`` is an optional argument here. It defaults to
   ``cms,lms,common``.

.. _diff-cover: https://github.com/Bachmann1234/diff-cover


JavaScript Code Style Quality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To view JavaScript code style quality run this command::

    paver run_eslint

-  This command also comes with a ``--limit`` switch, this is an example of that switch::

    paver run_eslint --limit=50000


Code Complexity Tools
=====================

Tool(s) available for evaluating complexity of edx-platform code:


- `plato <https://github.com/es-analysis/plato>`__ for JavaScript code
  complexity. Several options are available on the command line; see
  documentation.  Below, the following command will produce an HTML report in a
  subdirectory called "jscomplexity"::

       plato -q -x common/static/js/vendor/ -t common -e .eslintrc.json -r -d jscomplexity common/static/js/

Other Testing Tips
==================

Connecting to Browser
---------------------

If you want to see the browser being automated for JavaScript,
you can connect to the container running it via VNC.

+------------------------+----------------------+
| Browser                | VNC connection       |
+========================+======================+
| Firefox (Default)      | vnc://0.0.0.0:25900  |
+------------------------+----------------------+
| Chrome (via Selenium)  | vnc://0.0.0.0:15900  |
+------------------------+----------------------+

On macOS, enter the VNC connection string in Safari to connect via VNC. The VNC
passwords for both browsers are randomly generated and logged at container
startup, and can be found by running ``make vnc-passwords``.

Most tests are run in Firefox by default.  To use Chrome for tests that normally
use Firefox instead, prefix the test command with
``SELENIUM_BROWSER=chrome SELENIUM_HOST=edx.devstack.chrome``

Factories
---------

Many tests delegate set-up to a "factory" class. For example, there are
factories for creating courses, problems, and users. This encapsulates
set-up logic from tests.

Factories are often implemented using `FactoryBoy`_.

In general, factories should be located close to the code they use. For
example, the factory for creating problem XML definitions is located in
``xmodule/capa/tests/response_xml_factory.py`` because the
``capa`` package handles problem XML.

.. _FactoryBoy: https://readthedocs.org/projects/factoryboy/

Running Tests on Paver Scripts
------------------------------

To run tests on the scripts that power the various Paver commands, use the following command::

  pytest pavelib

Testing using queue servers
---------------------------

When testing problems that use a queue server on AWS (e.g.
sandbox-xqueue.edx.org), you'll need to run your server on your public IP, like so::

    ./manage.py lms runserver 0.0.0.0:8000

When you connect to the LMS, you need to use the public ip. Use
``ifconfig`` to figure out the number, and connect e.g. to
``http://18.3.4.5:8000/``
