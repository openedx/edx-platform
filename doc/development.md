# Running the CMS

One can start the CMS by running `rake cms`. This will run the server on localhost
port 8001.

However, the server also needs data to work from.

## Installing Mongodb

Please see http://www.mongodb.org/downloads for more detailed instructions.

### Ubuntu

    sudo apt-get install mongodb

### OSX

Use the MacPorts package `mongodb` or the Homebrew formula `mongodb`

## Initializing Mongodb

Check out the course data directories that you want to work with into the
`GITHUB_REPO_ROOT` (by default, `../data`). Then run the following command:


    rake django-admin[import,cms,dev,../data]

Replace `../data` with your `GITHUB_REPO_ROOT` if it's not the default value.

This will import all courses in your data directory into mongodb

## Unit tests

This runs all the tests (long, uses collectstatic):

    rake test

If if you aren't changing static files, can run `rake test` once, then run

    rake fasttest_{lms,cms}

xmodule can be tested independently, with this:

    rake test_common/lib/xmodule

To see all available rake commands, do this:

    rake -T

To run a single django test class:

    django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/courseware/tests/tests.py:TestViewAuth

To run a single django test:

    django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/courseware/tests/tests.py:TestViewAuth.test_dark_launch


To run a single nose test file:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py

To run a single nose test:

    nosetests common/lib/xmodule/xmodule/tests/test_stringify.py:test_stringify


Very handy: if you uncomment the `--pdb` argument in `NOSE_ARGS` in `lms/envs/test.py`, it will drop you into pdb on error.  This lets you go up and down the stack and see what the values of the variables are.  Check out http://docs.python.org/library/pdb.html

## Content development

If you change course content, while running the LMS in dev mode, it is unnecessary to restart to refresh the modulestore.  

Instead, hit /migrate/modules to see a list of all modules loaded, and click on links (eg /migrate/reload/edx4edx) to reload a course.

### Gitreload-based workflow

github (or other equivalent git-based repository systems) used for
course content can be setup to trigger an automatic reload when changes are pushed.  Here is how:

1. Each content directory in mitx_all/data should be a clone of a git repo

2. The user running the mitx gunicorn process should have its ssh key registered with the git repo

3. The list settings.ALLOWED_GITRELOAD_IPS should contain the IP address of the git repo originating the gitreload request.
    By default, this list is ['207.97.227.253', '50.57.128.197', '108.171.174.178'] (the github IPs).
    The list can be overridden in the startup file used, eg lms/envs/dev*.py

4. The git post-receive-hook should POST to /gitreload with a JSON payload.  This payload should define at least

   { "repository" : { "name" : reload_dir }

    where reload_dir is the directory name of the content to reload (ie mitx_all/data/reload_dir should exist)

    The mitx server will then do "git reset --hard HEAD; git clean -f -d; git pull origin" in that directory.  After the pull,
    it will reload the modulestore for that course.
