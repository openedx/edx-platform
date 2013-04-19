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

    pip install -r requirements.txt


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

To run a single django test class:

    django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/courseware/tests/tests.py:TestViewAuth

To run a single django test:

    django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/courseware/tests/tests.py:TestViewAuth.test_dark_launch


To run a single nose test file:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py

To run a single nose test:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py:test_stringify


Very handy: if you uncomment the `pdb=1` line in `setup.cfg`, it will drop you into pdb on error.  This lets you go up and down the stack and see what the values of the variables are.  Check out [the pdb documentation](http://docs.python.org/library/pdb.html)

### Running Javascript Unit Tests

These commands start a development server with jasmine testing enabled, and launch your default browser
pointing to those tests

    rake browse_jasmine_{lms,cms}

To run the tests headless, you must install [phantomjs](http://phantomjs.org/download.html), then run:

    rake phantomjs_jasmine_{lms,cms}

If the `phantomjs` binary is not on the path, set the `PHANTOMJS_PATH` environment variable to point to it

    PHANTOMJS_PATH=/path/to/phantomjs rake phantomjs_jasmine_{lms,cms}

Once you have run the `rake` command, your browser should open to 
to `http://localhost/_jasmine/`, which displays the test results.

**Troubleshooting**: If you get an error message while running the `rake` task,
try running `bundle install` to install the required ruby gems.

### Running Acceptance Tests

We use [Lettuce](http://lettuce.it/) for acceptance testing.
Most of our tests use [Splinter](http://splinter.cobrateam.info/)
to simulate UI browser interactions.  Splinter, in turn,
uses [Selenium](http://docs.seleniumhq.org/) to control the browser.

**Prerequisite**: You must have [ChromeDriver](https://code.google.com/p/selenium/wiki/ChromeDriver) 
installed to run the tests in Chrome.  

Before running the tests, you need to set up the test database:

    rm ../db/test_mitx.db
    rake django-admin[syncdb,lms,acceptance,--noinput]
    rake django-admin[migrate,lms,acceptance,--noinput]

To run the acceptance tests:

1. Start the Django server locally using the settings in **acceptance.py**:

        rake lms[acceptance]

2. In another shell, run the tests:

        django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=. lms/djangoapps/portal/features/

To test only a specific feature:

    django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=. lms/djangoapps/courseware/features/high-level-tabs.feature

**Troubleshooting**: If you get an error message that says something about harvest not being a command, you probably are missing a requirement.
Try running:

    pip install -r requirements.txt


## Viewing Test Coverage

We currently collect test coverage information for Python unit/integration tests.

To view test coverage:

1. Run the test suite:

        rake test

2. Generate reports:

        rake coverage:html

3. HTML reports are located in the `reports` folder.


## Testing using queue servers

When testing problems that use a queue server on AWS (e.g. sandbox-xqueue.edx.org), you'll need to run your server on your public IP, like so.

`django-admin.py runserver --settings=lms.envs.dev --pythonpath=. 0.0.0.0:8000`

When you connect to the LMS, you need to use the public ip.  Use `ifconfig` to figure out the number, and connect e.g. to `http://18.3.4.5:8000/`
