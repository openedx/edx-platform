# Development Tasks

## Prerequisites

### Ruby

To install all of the libraries needed for our rake commands, run `bundle install`.
This will read the `Gemfile` and install all of the gems specified there.

### Python

Run the following::

    pip install -r requirements.txt

### Binaries

Install the following:

* Mongodb (http://www.mongodb.org/)

### Databases

First start up the mongo daemon. E.g. to start it up in the background
using a config file:

    mongod --config /usr/local/etc/mongod.conf &

Check out the course data directories that you want to work with into the
`GITHUB_REPO_ROOT` (by default, `../data`). Then run the following command:

    rake resetdb

## Installing

To create your development environment, run the shell script in the root of
the repo:

    scripts/create-dev-env.sh


## Starting development servers

Both the LMS and Studio can be started using the following shortcut tasks

    rake lms  # Start the LMS
    rake cms  # Start studio
    rake lms[cms.dev]  # Start LMS to run alongside Studio
    rake lms[cms.dev_preview]  # Start LMS to run alongside Studio in preview mode

Under the hood, this executes `django-admin.py runserver --pythonpath=$WORKING_DIRECTORY --settings=lms.envs.dev`,
which starts a local development server.

Both of these commands take arguments to start the servers in different environments
or with additional options:

    # Start the LMS using the test configuration, on port 5000
    rake lms[test,5000]  # Executes django-admin.py runserver --pythonpath=$WORKING_DIRECTORY --setings=lms.envs.test 5000

*N.B.* You may have to escape the `[` characters, depending on your shell: `rake "lms[test,5000]"`

To get a full list of available rake tasks, use:

    rake -T

## Running Tests

See `testing.md` for instructions on running the test suite.

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

Note that the gitreload-based workflow is not meant for deployments on AWS (or elsewhere) which use collectstatic, since collectstatic is not run by a gitreload event.

Also, the gitreload feature needs MITX_FEATURES['ENABLE_LMS_MIGRATION'] = True in the django settings.

