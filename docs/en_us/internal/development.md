# Development Tasks

## Prerequisites

### Ruby

To install all of the required ruby libraries, run `bundle install`.
This will read the `Gemfile` and install all of the gems specified there.

### Python

Run the following::

    pip install -r requirements.txt

### Binaries

Install the following:

* Mongodb (http://www.mongodb.org/)

### Databases

First start up the MongoDB daemon. E.g. to start it up in the background
using a config file (sometimes using `sudo` is required):

    mongod --config /usr/local/etc/mongod.conf &

On some Linux distributions the configuration script is located at:

    /etc/mongodb.conf

If MongoDB does not start properly, it might be the case that there is a stray
lock file somewhere, or that the configuration file is corrupt. In this case
try deleting the lock files, and then running the MongoDB repair script:

    sudo rm -rf /data/db/mongod.lock
    sudo rm -rf /var/lib/mongodb/mongod.lock
    sudo -u mongodb mongod -f /usr/local/etc/mongod.conf --repair

To verify that MongoDB started up OK, run the MongoDB client:

    mongo

After MongoDB daemon is successfully running, check out the course data
directories that you want to work with into the `GITHUB_REPO_ROOT` (by default,
`../data`). Then run the following command:

    paver update_db

## Installing

To create your development environment, run the shell script in the root of
the repo:

    scripts/create-dev-env.sh


## Starting development servers

Both the LMS and Studio can be started using the following shortcut tasks

    paver lms  # Start the LMS
    paver studio  # Start studio
    paver lms --settings=cms.dev  # Start LMS to run alongside Studio
    paver lms --settings=cms.dev_preview  # Start LMS to run alongside Studio in preview mode

Under the hood, this executes `./manage.py {lms|cms} --settings $ENV runserver`,
which starts a local development server.

Both of these commands take arguments to start the servers in different environments
or with additional options:

    # Start the LMS using the test configuration, on port 5000
    paver lms --settings=test --port=5000  # Executes ./manage.py lms --settings test runserver 5000

To get a full list of available paver tasks, run:

     paver --help


### Troubleshooting

#### Reference Error: XModule is not defined (javascript)
This means that the javascript defining an xmodule hasn't loaded correctly. There are a number
of different things that could be causing this:

1. See `Error: watch EMFILE`

#### Error: watch EMFILE (coffee)
When running a development server, we also start a watcher process alongside to recompile coffeescript
and sass as changes are made. On Mac OSX systems, the coffee watcher process takes more file handles
than are allowed by default. This will result in `EMFILE` errors when coffeescript is running, and
will prevent javascript from compiling, leading to the error 'XModule is not defined'

To work around this issue, we use `Process::setrlimit` to set the number of allowed open files.
Coffee watches both directories and files, so you will need to set this fairly high (anecdotally,
8000 seems to do the trick on OSX 10.7.5, 10.8.3, and 10.8.4)


## Running Tests

See `testing.rst` for instructions on running the test suite.

## Content development

If you change course content, while running the LMS in dev mode, it is unnecessary to restart to refresh the modulestore.

Instead, hit /migrate/modules to see a list of all modules loaded, and click on links (eg /migrate/reload/edx4edx) to reload a course.

### Gitreload-based workflow

github (or other equivalent git-based repository systems) used for
course content can be setup to trigger an automatic reload when changes are pushed.  Here is how:

1. Each content directory in edx_all/data should be a clone of a git repo

2. The user running the edx gunicorn process should have its ssh key registered with the git repo

3. The list settings.ALLOWED_GITRELOAD_IPS should contain the IP address of the git repo originating the gitreload request.
    By default, this list is ['207.97.227.253', '50.57.128.197', '108.171.174.178'] (the github IPs).
    The list can be overridden in the startup file used, eg lms/envs/dev*.py

4. The git post-receive-hook should POST to /gitreload with a JSON payload.  This payload should define at least

   { "repository" : { "name" : reload_dir }

    where reload_dir is the directory name of the content to reload (ie edx_all/data/reload_dir should exist)

    The edx server will then do "git reset --hard HEAD; git clean -f -d; git pull origin" in that directory.  After the pull,
    it will reload the modulestore for that course.

Note that the gitreload-based workflow is not meant for deployments on AWS (or elsewhere) which use collectstatic, since collectstatic is not run by a gitreload event.

Also, the gitreload feature needs FEATURES['ENABLE_LMS_MIGRATION'] = True in the django settings.

