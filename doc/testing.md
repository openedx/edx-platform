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

Before running tests, ensure that you have all the dependencies.  You can install dependencies using:

    rake install_prereqs


## Running Python Unit tests

We use [nose](https://nose.readthedocs.org/en/latest/) through
the [django-nose plugin](https://pypi.python.org/pypi/django-nose)
to run the test suite.

You can run tests using `rake` commands.  For example,

    rake test

runs all the tests.  It also runs `collectstatic`, which prepares the static files used by the site (for example, compiling Coffeescript to Javascript).

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

    rake test_lms[courseware.tests.tests:testViewAuth]

To run a single django test:

    rake test_lms[courseware.tests.tests:TestViewAuth.test_dark_launch]

To run a single nose test file:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py

To run a single nose test:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py:test_stringify


Very handy: if you uncomment the `pdb=1` line in `setup.cfg`, it will drop you into pdb on error.  This lets you go up and down the stack and see what the values of the variables are.  Check out [the pdb documentation](http://docs.python.org/library/pdb.html)

### Running Javascript Unit Tests

To run all of the javascript unit tests, use

    rake jasmine

If the `phantomjs` binary is on the path, or the `PHANTOMJS_PATH` environment variable is
set to point to it, then the tests will be run headless. Otherwise, they will be run in
your default browser

    export PATH=/path/to/phantomjs:$PATH
    rake jasmine  # Runs headless

or

    PHANTOMJS_PATH=/path/to/phantomjs rake jasmine  # Runs headless

or

    rake jasmine  # Runs in browser

You can also force a run using phantomjs or the browser using the commands

    rake jasmine:browser  # Runs in browser
    rake jasmine:phantomjs  # Runs headless

You can run tests for a specific subsystems as well

    rake jasmine:lms  # Runs all lms javascript unit tests using the default method
    rake jasmine:cms:browser  # Runs all cms javascript unit tests in the browser

Use `rake -T` to get a list of all available subsystems

**Troubleshooting**: If you get an error message while running the `rake` task,
try running `bundle install` to install the required ruby gems.

Unit tests can be run in parallel to each other and while acceptance tests are running

### Running Acceptance Tests

We use [Lettuce](http://lettuce.it/) for acceptance testing.
Most of our tests use [Splinter](http://splinter.cobrateam.info/)
to simulate UI browser interactions.  Splinter, in turn,
uses [Selenium](http://docs.seleniumhq.org/) to control the Chrome browser.

**Prerequisite**: You must have [ChromeDriver](https://code.google.com/p/selenium/wiki/ChromeDriver)
installed to run the tests in Chrome.  The tests are confirmed to run
with Chrome (not Chromium) version 26.0.0.1410.63 with ChromeDriver
version r195636.

To run all the acceptance tests:

    rake test_acceptance_lms
    rake test_acceptance_cms

To test only a specific feature:

    rake test_acceptance_lms[lms/djangoapps/courseware/features/problems.feature]

To start the debugger on failure, add the `--pdb` option:

    rake test_acceptance_lms["lms/djangoapps/courseware/features/problems.feature --pdb"]

To run tests faster by not collecting static files, you can use
`rake fasttest_acceptance_lms` and `rake fasttest_acceptance_cms`.

Acceptance tests will run on a randomized port and can be run in the background of rake cms and lms or unit tests.
To specify the port, change the LETTUCE_SERVER_PORT constant in cms/envs/acceptance.py and lms/envs/acceptance.py
as well as the port listed in cms/djangoapps/contentstore/feature/upload.py

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

1. Do not assert not if possible for css.  Use world.is_css_present and is_css_not_present
    Errors can arise if checks for the css are performed before the page finishes loading.
    To get around this, there are functions that will wait a period of time for the css to appear
    before returning and return immediately if they are there.  There is a reverse to this function as well.
    It will wait for the css to not appear and returns if it isn't there.

    All css functions can utilize this timeout to ensure that the page is fully loaded

2. Dealing with alerts
    Chrome can hang on javascripts alerts.  If a javascript alert/prompt/confirmation is expected, use the step
    'I will confirm all alerts', 'I will cancel all alerts' or 'I will anser all prompts with "(.*)"' before the step
    that causes the alert in order to properly deal with it.

3. Dealing with stale element reference exceptions
    These exceptions happen if any part of the page is refreshed in between finding an element and accessing the element.
    When possible, use any of the css functions in common/djangoapps/terrain/ui_helpers.py as they will retry the action
    in case of this exception.  If the functionality is not there, wrap the function with world.retry_on_exception.  This function takes in a function and will retry and return the result of the function if there was an exception

4. Scenario Level Constants
    If you want an object to be available for the entire scenario, it can be stored in world.scenario_dict.  This object
    is a dictionary that gets refreshed at the beginning on the scenario.  Currently, the current logged in user and the current created course are stored under 'COURSE' and 'USER'.  This will help prevent strings from being hard coded so the
    acceptance tests can become more flexible.

