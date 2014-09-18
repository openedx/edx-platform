# Testing

## Overview

We maintain three kinds of tests: unit tests, integration tests,
and acceptance tests.

Overall, you want to write the tests that **maximize coverage**
while **minimizing maintenance**.
In practice, this usually means investing heavily
in unit tests, which tend to be the most robust to changes in the code base.

![Test Pyramid](test_pyramid.png)

The pyramid above shows the relative number of unit tests, integration tests,
and acceptance tests.  Most of our tests are unit tests or integration tests.

### Unit Tests

* Each test case should be concise: setup, execute, check, and teardown.
If you find yourself writing tests with many steps, consider refactoring
the unit under tests into smaller units, and then testing those individually.

* As a rule of thumb, your unit tests should cover every code branch.

* Mock or patch external dependencies.
We use [voidspace mock](http://www.voidspace.org.uk/python/mock/).

* We unit test Python code (using [unittest](http://docs.python.org/2/library/unittest.html)) and
Javascript (using [Jasmine](http://jasmine.github.io/))

### Integration Tests
* Test several units at the same time.
Note that you can still mock or patch dependencies
that are not under test!  For example, you might test that
`LoncapaProblem`, `NumericalResponse`, and `CorrectMap` in the
`capa` package work together, while still mocking out template rendering.

* Use integration tests to ensure that units are hooked up correctly.
You do not need to test every possible input--that's what unit
tests are for.  Instead, focus on testing the "happy path"
to verify that the components work together correctly.

* Many of our tests use the [Django test client](https://docs.djangoproject.com/en/dev/topics/testing/overview/)
to simulate HTTP requests to the server.

### UI Acceptance Tests
* Use these to test that major program features are working correctly.

* We use [lettuce](http://lettuce.it/) to write BDD-style tests.  Most of
these tests simulate user interactions through the browser using
[splinter](http://splinter.cobrateam.info/).

* We use [Bok Choy](http://bok-choy.readthedocs.org/en/latest/tutorial.html) to 
write end-user acceptance tests directly in Python, using the framework to 
maximize reliability and maintainability.

## Test Locations

* Python unit and integration tests: Located in
subpackages called `tests`.
For example, the tests for the `capa` package are located in
`common/lib/capa/capa/tests`.

* Javascript unit tests: Located in `spec` folders.  For example,
`common/lib/xmodule/xmodule/js/spec` and `{cms,lms}/static/coffee/spec`
For consistency, you should use the same directory structure for implementation
and test.  For example, the test for `src/views/module.coffee`
should be written in `spec/views/module_spec.coffee`.

* UI acceptance tests:
    - Set up and helper methods, and stubs for external services: `common/djangoapps/terrain`
    - Lettuce Tests: located in `features` subpackage within a Django app.
    For example: `lms/djangoapps/courseware/features`
    - Bok Choy Tests: Artifacts are located under `common/test/acceptance`


## Factories

Many tests delegate set-up to a "factory" class.  For example,
there are factories for creating courses, problems, and users.
This encapsulates set-up logic from tests.

Factories are often implemented using [FactoryBoy](https://readthedocs.org/projects/factoryboy/)

In general, factories should be located close to the code they use.
For example, the factory for creating problem XML definitions
 is located in `common/lib/capa/capa/tests/response_xml_factory.py`
because the `capa` package handles problem XML.


# Running Tests

You can run all of the unit-level tests using the command

    paver test

This includes python, javascript, and documentation tests. It does not, however,
run any acceptance tests.

## Running Python Unit tests

We use [nose](https://nose.readthedocs.org/en/latest/) through
the [django-nose plugin](https://pypi.python.org/pypi/django-nose)
to run the test suite.

You can run all the python tests using `paver` commands.  For example,

    paver test_python

runs all the tests.  It also runs `collectstatic`, which prepares the static files used by the site (for example, compiling Coffeescript to Javascript).

You can re-run all failed python tests by running: (see note at end of section)

    paver test_python --failed

To test lms or cms python, use:

    paver test_system -s lms

or

    paver test_system -s cms

You can also run these tests without `collectstatic`, which is faster:

    paver test_system -s lms --fasttest

or

    paver test_system -s cms --fasttest

To run a single django test class:

    paver test_system -t lms/djangoapps/courseware/tests/tests.py:ActivateLoginTest
    
When developing tests, it is often helpful to be able to really just run one single test without the overhead of PIP installs, UX builds, etc. In this case, it is helpful to look at the output of paver, and run just the specific command (optionally, stripping away coverage metrics). At the time of this writing, the command is: 

    python ./manage.py lms test --verbosity=1 lms/djangoapps/courseware/tests/test_courses.py   --traceback --settings=test

To run a single django test:

    paver test_system -t lms/djangoapps/courseware/tests/tests.py:ActivateLoginTest.test_activate_login
    
To re-run all failing django tests from lms or cms, use the `--failed`,`-f` flag (see note at end of section)

    paver test_system -s lms --failed
    paver test_system -s cms --failed

There is also a `--fail_fast`, `-x` option that will stop nosetests after the first failure.

common/lib tests are tested with the `test_lib` task, which also accepts the `--failed` and `--fail_fast` options. For example:

    paver test_lib -l common/lib/calc

or

    paver test_lib -l common/lib/xmodule --failed

To run a single nose test file:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py

To run a single nose test:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py:test_stringify

To run a single test and get stdout, with proper env config:

    python manage.py cms --settings test test contentstore.tests.test_import_nostatic -s

To run a single test and get stdout and get coverage:

    python -m coverage run --rcfile=./common/lib/xmodule/.coveragerc which ./manage.py cms --settings test test --traceback --logging-clear-handlers --liveserver=localhost:8000-9000 contentstore.tests.test_import_nostatic -s # cms example
    python -m coverage run --rcfile=./lms/.coveragerc which ./manage.py lms --settings test test --traceback --logging-clear-handlers --liveserver=localhost:8000-9000  courseware.tests.test_module_render -s # lms example

generate coverage report:

    coverage report --rcfile=./common/lib/xmodule/.coveragerc

or to get html report:

    coverage html --rcfile=./common/lib/xmodule/.coveragerc

then browse reports/common/lib/xmodule/cover/index.html

To run tests for stub servers, for example for
[YouTube stub server](https://github.com/edx/edx-platform/blob/master/common/djangoapps/terrain/stubs/tests/test_youtube_stub.py),
you can do one of:

    paver test_system -s cms -t common/djangoapps/terrain/stubs/tests/test_youtube_stub.py
    python -m coverage run --rcfile=cms/.coveragerc `which ./manage.py` cms --settings test test --traceback common/djangoapps/terrain/stubs/tests/test_youtube_stub.py


Very handy: if you uncomment the `pdb=1` line in `setup.cfg`, it will drop you into pdb on error.  This lets you go up and down the stack and see what the values of the variables are.  Check out [the pdb documentation](http://docs.python.org/library/pdb.html)


Note: More on the `--failed` functionality
* In order to use this, you must run the tests first. If you haven't already run the tests, or if no tests failed in the previous run, then using the `--failed` switch will result in **all** of the tests being run.  See more about this in the [nose documentation](http://nose.readthedocs.org/en/latest/plugins/testid.html#looping-over-failed-tests).
* Note that `paver test_python` calls nosetests separately for cms and lms. This means that if tests failed only in lms on the previous run, then calling `paver test_python --failed` will run **all of the tests for cms** in addition to the previously failing lms tests. If you want it to run only the failing tests for lms or cms, use the `paver test_system -s lms --failed` or `paver test_system -s cms --failed` commands. 


### Running Javascript Unit Tests

We use Jasmine to run JavaScript unit tests.  To run all the JavaScript tests:

    paver test_js

To run a specific set of JavaScript tests and print the results to the console:

    paver test_js_run -s lms
    paver test_js_run -s cms
    paver test_js_run -s cms-squire
    paver test_js_run -s xmodule
    paver test_js_run -s common

To run JavaScript tests in your default browser:

    paver test_js_dev -s lms
    paver test_js_dev -s cms
    paver test_js_dev -s cms-squire
    paver test_js_dev -s xmodule
    paver test_js_dev -s common


These paver commands call through to a custom test runner.  For more info, see [js-test-tool](https://github.com/edx/js-test-tool).


### Running Bok Choy Acceptance Tests

We use [Bok Choy](http://bok-choy.readthedocs.org/en/latest/tutorial.html) for acceptance testing.
Bok Choy is a UI-level acceptance test framework for writing robust [Selenium](http://docs.seleniumhq.org/) tests in [Python](https://www.python.org/).
Bok Choy makes your acceptance tests reliable and maintainable by utilizing the Page Object and Promise design patterns.

**Prerequisites**: 
* These prerequisites are all automatically installed and available in [Devstack](https://github.com/edx/configuration/wiki/edX-Developer-Stack), 
the supported development enviornment for the edX Platform.
* Chromedriver and Chrome (see Running Lettuce Acceptance Tests below for the latest tested versions)
* Mongo
* Memcache
* mySQL


To run all the bok choy acceptance tests:

    paver test_bokchoy

Once the database has been set up and the static files collected, you can use the 'fast' 
option to skip those tasks. This option can also be used with any of the test specs below:

    paver test_bokchoy --fasttest

To run single test, specify the name of the test file. For example:

    paver test_bokchoy -t test_lms.py

To run single test faster by not repeating setup tasks:

    paver test_bokchoy -t test_lms.py --fasttest

To test only a certain feature, specify the file and the testcase class:

    paver test_bokchoy -t test_lms.py:RegistrationTest

To execute only a certain test case, specify the file name, class, and 
test case method:

    paver test_bokchoy -t test_lms.py:RegistrationTest.test_register

During acceptance test execution, log files and also screenshots of failed tests
are captured in test_root/log.

To put a debugging breakpoint in a test use:

    from nose.tools import set_trace; set_trace()


### Running Lettuce Acceptance Tests

We use [Lettuce](http://lettuce.it/) for acceptance testing.
Most of our tests use [Splinter](http://splinter.cobrateam.info/)
to simulate UI browser interactions.  Splinter, in turn,
uses [Selenium](http://docs.seleniumhq.org/) to control the Chrome browser.

**Prerequisite**: You must have [ChromeDriver](https://code.google.com/p/selenium/wiki/ChromeDriver)
installed to run the tests in Chrome.  The tests are confirmed to run
with Chrome (not Chromium) version 34.0.1847.116 with ChromeDriver version 2.6.232917.

To run all the acceptance tests:
    paver test_acceptance

To run only for lms or cms:

    paver test_acceptance -s lms
    paver test_acceptance -s cms

To test only a specific feature:

    paver test_acceptance -s lms --extra_args="lms/djangoapps/courseware/features/problems.feature"

To test only a specific scenario

    paver test_acceptance -s lms --extra_args="lms/djangoapps/courseware/features/problems.feature -s 3"

To start the debugger on failure, add the `--pdb` option to extra_args:

    paver test_acceptance -s lms --extra_args="lms/djangoapps/courseware/features/problems.feature --pdb"

To run tests faster by not collecting static files, you can use
`paver test_acceptance -s lms --fasttest` and `paver test_acceptance -s cms --fasttest`.

Acceptance tests will run on a randomized port and can be run in the background of paver cms and lms or unit tests.
To specify the port, change the LETTUCE_SERVER_PORT constant in cms/envs/acceptance.py and lms/envs/acceptance.py
as well as the port listed in cms/djangoapps/contentstore/feature/upload.py

During acceptance test execution, Django log files are written to `test_root/log/lms_acceptance.log` and `test_root/log/cms_acceptance.log`.

**Note**: The acceptance tests can *not* currently run in parallel.

### Debugging Acceptance Tests on Vagrant

If you are using a local Vagrant dev environment to run acceptance tests, then you will only get console text output. To actually see what is happening, you can turn on automatic screenshots. For each step two screenshots will be taken - before, and after. To do this, simply add the step:

    Given I enable capturing of screenshots before and after each step

to your scenario. This step can be added anywhere, and will enable automatic screenshots for all following steps for that scenario only. You can also use the step

    Given I disable capturing of screenshots before and after each step

to turn off auto screenshots for all steps following it.

Screenshots will be placed in the folder `{TEST_ROOT}/log/auto_screenshots`. Each time you launch acceptance tests, this folder will be cleaned. Each screenshot will be named according to the template string `{scenario_number}__{step_number}__{step_function_name}__{"1_before"|"2_after"}`.

If you don't want to have screenshots be captured for all steps, but rather want fine grained control, you can use the decorator

    @capture_screenshot_before_after

before any Python function in `feature_name.py` file. The decorator will capture two screenshots - one before the decorated function runs, and one after. Also, the function

    from lettuce import world; world.capture_screenshot("image_name")

is available, and can be inserted at any point in code to capture a screenshot specifically in that place. In both cases the captured screenshots will go to the same folder as when using the step method - `{TEST_ROOT}/log/auto_screenshot`.

A totally different approach to visually seeing acceptance tests run in Vagrant is to redirect Vagrant X11 session to your local machine. Please see https://github.com/edx/edx-platform/wiki/Test-engineering-FAQ for instruction on how to achieve this.

## Viewing Test Coverage

We currently collect test coverage information for Python unit/integration tests.

To view test coverage:

1. Run the test suite:

        paver test

2. Generate reports:

        paver coverage

3. Reports are located in the `reports` folder.  The command
generates HTML and XML (Cobertura format) reports.


## Code Style Quality

To view code style quality (e.g. pep8 and pylint violations):

    paver run_quality


## Testing using queue servers

When testing problems that use a queue server on AWS (e.g. sandbox-xqueue.edx.org), you'll need to run your server on your public IP, like so.

`./manage.py lms runserver 0.0.0.0:8000`

When you connect to the LMS, you need to use the public ip.  Use `ifconfig` to figure out the number, and connect e.g. to `http://18.3.4.5:8000/`


## Acceptance Test Techniques

1. Element existence on the page<br />
    Do not use splinter's built-in browser methods directly for determining if elements exist.
    Use the world.is_css_present and world.is_css_not_present wrapper functions instead.
    Otherwise errors can arise if checks for the css are performed before the page finishes loading.
    Also these wrapper functions are optimized for the amount of wait time spent in both cases of positive
    and negative expectation.

2. Dealing with alerts<br />
    Chrome can hang on javascripts alerts.  If a javascript alert/prompt/confirmation is expected, use the step
    'I will confirm all alerts', 'I will cancel all alerts' or 'I will anser all prompts with "(.*)"' before the step
    that causes the alert in order to properly deal with it.

3. Dealing with stale element reference exceptions<br />
    These exceptions happen if any part of the page is refreshed in between finding an element and accessing the element.
    When possible, use any of the css functions in common/djangoapps/terrain/ui_helpers.py as they will retry the action
    in case of this exception.  If the functionality is not there, wrap the function with world.retry_on_exception.  This function takes in a function and will retry and return the result of the function if there was an exception

4. Scenario Level Constants<br />
    If you want an object to be available for the entire scenario, it can be stored in world.scenario_dict.  This object
    is a dictionary that gets refreshed at the beginning on the scenario.  Currently, the current logged in user and the current created course are stored under 'COURSE' and 'USER'.  This will help prevent strings from being hard coded so the
    acceptance tests can become more flexible.

5. Internal edX Jenkins considerations<br />
    Acceptance tests are run in Jenkins as part of the edX development workflow. They are broken into shards and split across
    workers. Therefore if you add a new .feature file, you need to define what shard they should be run in or else they
    will not get executed. See someone from TestEng to help you determine where they should go.

    Also, the test results are rolled up in Jenkins for ease of understanding, with the acceptance tests under the top level
    of "CMS" and "LMS" when they follow this convention: name your feature in the .feature file CMS or LMS with a single
    period and then no other periods in the name. The name can contain spaces. E.g. "CMS.Sign Up"
