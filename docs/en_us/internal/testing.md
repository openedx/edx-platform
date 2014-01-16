# Testing

## Overview

We maintain three kinds of tests: unit tests, integration tests,
and acceptance tests.

### Unit Tests

* Each test case should be concise: setup, execute, check, and teardown.
If you find yourself writing tests with many steps, consider refactoring
the unit under tests into smaller units, and then testing those individually.

* As a rule of thumb, your unit tests should cover every code branch.

* Mock or patch external dependencies.
We use [voidspace mock](http://www.voidspace.org.uk/python/mock/).

* We unit test Python code (using [unittest](http://docs.python.org/2/library/unittest.html)) and
Javascript (using [Jasmine](http://pivotal.github.io/jasmine/))

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

* Many of our tests use the [Django test client](https://docs.djangoproject.com/en/dev/topics/testing/overview/) to simulate
HTTP requests to the server.

### UI Acceptance Tests
* Use these to test that major program features are working correctly.

* We use [lettuce](http://lettuce.it/) to write BDD-style tests.  Most of
these tests simulate user interactions through the browser using
[splinter](http://splinter.cobrateam.info/).

Overall, you want to write the tests that **maximize coverage**
while **minimizing maintenance**.
In practice, this usually means investing heavily
in unit tests, which tend to be the most robust to changes in the code base.

![Test Pyramid](test_pyramid.png)

The pyramid above shows the relative number of unit tests, integration tests,
and acceptance tests.  Most of our tests are unit tests or integration tests.

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
    - Set up and helper methods: `common/djangoapps/terrain`
    - Tests: located in `features` subpackage within a Django app.
    For example: `lms/djangoapps/courseware/features`


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

    rake test

This includes python, javascript, and documentation tests. It does not, however,
run any acceptance tests.

## Running Python Unit tests

We use [nose](https://nose.readthedocs.org/en/latest/) through
the [django-nose plugin](https://pypi.python.org/pypi/django-nose)
to run the test suite.

You can run all the python tests using `rake` commands.  For example,

    rake test:python

runs all the tests.  It also runs `collectstatic`, which prepares the static files used by the site (for example, compiling Coffeescript to Javascript).

You can re-run all failed python tests by running

    rake test:python[--failed]

You can also run the tests without `collectstatic`, which tends to be faster:

    rake fasttest_lms

or

    rake fasttest_cms

xmodule can be tested independently, with this:

    rake test_common/lib/xmodule

other module level tests include

* `rake test_common/lib/capa`
* `rake test_common/lib/calc`

To run a single django test class:

    rake test_lms[lms/djangoapps/courseware/tests/tests.py:ActivateLoginTest]

To run a single django test:

    rake test_lms[lms/djangoapps/courseware/tests/tests.py:ActivateLoginTest.test_activate_login]

To re-run all failing django tests from lms or cms:

    rake test_lms[--failed]

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


Very handy: if you uncomment the `pdb=1` line in `setup.cfg`, it will drop you into pdb on error.  This lets you go up and down the stack and see what the values of the variables are.  Check out [the pdb documentation](http://docs.python.org/library/pdb.html)


### Running Javascript Unit Tests

We use Jasmine to run JavaScript unit tests.  To run all the JavaScript tests:

    rake test:js

To run a specific set of JavaScript tests and print the results to the console:

    rake test:js:run[lms]
    rake test:js:run[cms]
    rake test:js:run[xmodule]
    rake test:js:run[common]

To run JavaScript tests in your default browser:

    rake test:js:dev[lms]
    rake test:js:dev[cms]
    rake test:js:dev[xmodule]
    rake test:js:dev[common]

These rake commands call through to a custom test runner.  For more info, see [js-test-tool](https://github.com/edx/js-test-tool).


### Running Acceptance Tests

We use [Lettuce](http://lettuce.it/) for acceptance testing.
Most of our tests use [Splinter](http://splinter.cobrateam.info/)
to simulate UI browser interactions.  Splinter, in turn,
uses [Selenium](http://docs.seleniumhq.org/) to control the Chrome browser.

**Prerequisite**: You must have [ChromeDriver](https://code.google.com/p/selenium/wiki/ChromeDriver)
installed to run the tests in Chrome.  The tests are confirmed to run
with Chrome (not Chromium) version 28.0.1500.71 with ChromeDriver
version 2.1.210398.

To run all the acceptance tests:
    rake test:acceptance

To run only for lms or cms:

    rake test:acceptance:lms
    rake test:acceptance:cms

To test only a specific feature:

    rake test:acceptance:lms["lms/djangoapps/courseware/features/problems.feature"]

To test only a specific scenario

    rake test:acceptance:lms["lms/djangoapps/courseware/features/problems.feature -s 3"]

To start the debugger on failure, add the `--pdb` option:

    rake test:acceptance:lms["lms/djangoapps/courseware/features/problems.feature --pdb"]

To run tests faster by not collecting static files, you can use
`rake test:acceptance:lms:fast` and `rake test:acceptance:cms:fast`.

Acceptance tests will run on a randomized port and can be run in the background of rake cms and lms or unit tests.
To specify the port, change the LETTUCE_SERVER_PORT constant in cms/envs/acceptance.py and lms/envs/acceptance.py
as well as the port listed in cms/djangoapps/contentstore/feature/upload.py

During acceptance test execution, Django log files are written to `test_root/log/lms_acceptance.log` and `test_root/log/cms_acceptance.log`.

**Note**: The acceptance tests can *not* currently run in parallel.

## Viewing Test Coverage

We currently collect test coverage information for Python unit/integration tests.

To view test coverage:

1. Run the test suite:

        rake test

2. Generate reports:

        rake coverage

3. Reports are located in the `reports` folder.  The command
generates HTML and XML (Cobertura format) reports.


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
