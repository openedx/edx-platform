# Testing

Testing is good.  Here is some useful info about how we set up tests.
More info is [on the wiki](https://edx-wiki.atlassian.net/wiki/display/ENG/Test+Engineering)

## Backend code

- The python unit tests can be run via rake tasks. 
See development.md for more info on how to do this.

## Frontend code

### Jasmine

We're using Jasmine to unit/integration test the JavaScript files. 
More info [on the wiki](https://edx-wiki.atlassian.net/wiki/display/ENG/Jasmine)

All the specs are written in CoffeeScript to be consistent with the code.
To access the test cases, start the server using the settings file **jasmine.py** using this command:
    `rake django-admin[runserver,lms,jasmine,12345]`

Then navigate to `http://localhost:12345/_jasmine/` to see the test results.

All the JavaScript codes must have test coverage. Both CMS and LMS
has its own test directory in `{cms,lms}/static/coffee/spec`  If you haven't
written a JavaScript test before, you can look at those example files as a
starting point. Also, these materials might be helpful for you:

CMS Note: For consistency, you're advised to use the same directory structure
for implementation and test. For example, test for `src/views/module.coffee`
should be written in `spec/views/module_spec.coffee`.

* http://pivotal.github.com/jasmine
* http://railscasts.com/episodes/261-testing-javascript-with-jasmine?view=asciicast
* http://a-developer-life.blogspot.com/2011/05/jasmine-part-1-unit-testing-javascript.html

If you're finishing a feature that contains JavaScript code snippets and do not
sure how to test, please feel free to open up a pull request and asking people
for help. (However, the best way to do it would be writing your test first, then
implement your feature - Test Driven Development.)

### BDD style acceptance tests with Lettuce

We're using Lettuce for end user acceptance testing of features.
More info [on the wiki](https://edx-wiki.atlassian.net/wiki/display/ENG/Lettuce+Acceptance+Testing)

Lettuce is a port of Cucumber. We're using it to drive Splinter, which is a python wrapper to Selenium.
To execute the automated test scripts, you'll need to start up the django server separately, then launch the tests.
Do both use the settings file named **acceptance.py**.

What this will do is to use a sqllite database named mitx_all/db/test_mitx.db. 
That way it can be flushed etc. without messing up your dev db.
Note that this also means that you need to syncdb and migrate the db first before starting the server to initialize it if it does not yet exist.

1. Set up the test database (only needs to be done once):
    rm ../db/test_mitx.db
    rake django-admin[syncdb,lms,acceptance,--noinput]
    rake django-admin[migrate,lms,acceptance,--noinput]

2. Start up the django server separately in a shell
    rake lms[acceptance]

3. Then in another shell, run the tests in different ways as below. Lettuce comes with a new django-admin command called _harvest_. See the [lettuce django docs](http://lettuce.it/recipes/django-lxml.html) for more details.
* All tests in a specified feature folder: `django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=. lms/djangoapps/portal/features/`
* Only the specified feature's scenarios: `django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=. lms/djangoapps/courseware/features/high-level-tabs.feature`

4. Troubleshooting
* If you get an error msg that says something about harvest not being a command, you probably are missing a requirement. Pip install (test-requirements.txt) and/or brew install as needed.