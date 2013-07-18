This is the main edX platform which consists of LMS and Studio.

See [code.edx.org](http://code.edx.org/) for other parts of the edX code base.

Installation - The first time
=============================

The following instructions will help you to download and setup a virtual machine
with a minimal amount of steps, using Vagrant. It is recommended for a first
installation, as it will save you from many of the common pitfalls of the
installation process.

1. Make sure you have plenty of available disk space, >5GB
2. Install Git: http://git-scm.com/downloads
3. Install VirtualBox: https://www.virtualbox.org/wiki/Download_Old_Builds_4_2
   (you need version 4.2.12, as later/earlier versions might not work well with 
   Vagrant)
4. Install Vagrant: http://www.vagrantup.com/ (Vagrant 1.2.2 or later)
5. Open a terminal
6. Download the project: `git clone git://github.com/edx/edx-platform.git`
7. Enter the project directory: `cd edx-platform/`
8. (Windows only) Run the commands to 
   [deal with line endings and symlinks under Windows](https://github.com/edx/edx-platform/wiki/Simplified-install-with-vagrant#dealing-with-line-endings-and-symlinks-under-windows)
9. Start: `vagrant up`

The last step might require your host machine's administrator password to setup NFS.

Afterwards, it will download an image, install all the dependencies and configure
the VM. It will take a while, go grab a coffee.

Once completed, hopefully you should see a "Success!" message indicating that the
installation went fine. (If not, refer to the 
[troubleshooting section](https://github.com/edx/edx-platform/wiki/Simplified-install-with-vagrant#troubleshooting).)

Note: by default, the VM will get the IP `192.168.20.40`. If you need to use a 
different IP, you can edit the file `Vagrantfile`. If you have already started the 
VM with `vagrant up`, see "Stopping and restarting the VM" below to take the change 
into account.

Accessing the VM
----------------

Once the installation is finished, to log into the virtual machine:

```
$ vagrant ssh
```

Note: This won't work from Windows, install install PuTTY from
http://www.chiark.greenend.org.uk/%7Esgtatham/putty/download.html instead. Then
connect to 127.0.0.1, port 2222, using vagrant/vagrant as a user/password.

Using edX
---------

Once inside the VM, you can start Studio and LMS with the following commands
(from the `/opt/edx/edx-platform` folder):

Learning management system (LMS):

```
$ rake lms[cms.dev,0.0.0.0:8000]
```

Studio:

```
$ rake cms[dev,0.0.0.0:8001]
```

Once started, open the following URLs in your browser:

* Learning management system (LMS): http://192.168.20.40:8000/
* Studio (CMS): http://192.168.20.40:8001/

You can develop by editing the files directly in the `edx-platform/` directory you
downloaded before, you don't need to connect to the VM to edit them (the VM uses
those files to run edX, mirroring the folder in `/opt/edx/edx-platform`).

You may also want to create a super-user with:

```
$ rake django-admin["createsuperuser"]
```

Also note that if you register a new user through the web interface,
the activiation email will be posted to your VM's terminal window (search for
lines similar to):

```
Subject: Your account for edX Studio
From: registration@edx.org
```

and find the activation URL for the account you've created.

See the [Frequently Asked Questions](https://github.com/edx/edx-platform/wiki/Frequently-Asked-Questions)
for more usage tips.

Stopping & starting
-------------------

To stop the VM (from your `edx-platform/` directory):

```
$ vagrant halt
```

To restart:

```
$ vagrant up
```

or, to start without attempting to update the dependencies:

```
$ vagrant up --no-provision
```

Troubleshooting
---------------

If anything doesn't work as expected, see the 
[troubleshooting section](https://github.com/edx/edx-platform/wiki/Simplified-install-with-vagrant#troubleshooting).

Installation - Advanced
=======================

Note: The following installation instructions are for advanced users & developers
who are familiar with setting up Python, Ruby & node.js virtual environments.
Even if you know what you are doing, edX has a large code base with multiple
dependencies, so you might still want to use the method described above the
first time, as Vagrant helps avoiding issues due to the different environments.

There is a `scripts/create-dev-env.sh` that will attempt to set up a development
environment.

If you want to better understand what the script is doing, keep reading.

Directory Hierarchy
-------------------

This code assumes that it is checked out in a directory that has three sibling
directories: `data` (used for XML course data), `db` (used to hold a
[sqlite](https://sqlite.org/) database), and `log` (used to hold logs). If you
clone the repository into a directory called `edx` inside of a directory
called `dev`, here's an example of how the directory hierarchy should look:

    * dev
     \
      * data
      * db
      * log
      * edx
       \
        README.md

Language Runtimes
-----------------
You'll need to be sure that you have Python 2.7, Ruby 1.9.3, and NodeJS
(latest stable) installed on your system. Some of these you can install
using your system's package manager: [homebrew](http://mxcl.github.io/homebrew/)
for Mac, [apt](http://wiki.debian.org/Apt) for Debian-based systems
(including Ubuntu), [rpm](http://www.rpm.org/) or [yum](http://yum.baseurl.org/)
for Red Hat based systems (including CentOS).

If your system's package manager gives you the wrong version of a language
runtime, then you'll need to use a versioning tool to install the correct version.
Usually, you'll need to do this for Ruby: you can use
[`rbenv`](https://github.com/sstephenson/rbenv) or [`rvm`](https://rvm.io/), but
typically `rbenv` is simpler. For Python, you can use
[`pythonz`](http://saghul.github.io/pythonz/),
and for Node, you can use [`nvm`](https://github.com/creationix/nvm).

Virtual Environments
--------------------
Often, different projects will have conflicting dependencies: for example, two
projects depending on two different, incompatible versions of a library. Clearly,
you can't have both versions installed and used on your machine simultaneously.
Virtual environments were created to solve this problem: by installing libraries
into an isolated environment, only projects that live inside the environment
will be able to see and use those libraries. Got incompatible dependencies? Use
different virtual environments, and your problem is solved.

Remember, each language has a different implementation. Python has
[`virtualenv`](http://www.virtualenv.org/), Ruby has
[`bundler`](http://gembundler.com/), and Node's virtual environment support
is built into [`npm`](https://npmjs.org/), its library management tool.
For each language, decide if you want to use a virtual environment, or if you
want to install all the language dependencies globally (and risk conflicts).
I suggest you start with installing things globally until and unless things
break; you can always switch over to a virtual environment later on.

Language Packages
-----------------
The Python libraries we use are listed in `requirements.txt`. The Ruby libraries
we use are listed in `Gemfile`. The Node libraries we use are listed in
`packages.json`. Python has a library installer called
[`pip`](http://www.pip-installer.org/), Ruby has a library installer called
[`gem`](https://rubygems.org/) (or `bundle` if you're using a virtual
environment), and Node has a library installer called
[`npm`](https://npmjs.org/).
Once you've got your languages and virtual environments set up, install
the libraries like so:

    $ pip install -r requirements/edx/pre.txt
    $ pip install -r requirements/edx/base.txt
    $ pip install -r requirements/edx/post.txt
    $ bundle install
    $ npm install

You can also use [`rake`](http://rake.rubyforge.org/) to get all of the prerequisites (or to update)
them if they've changed

    $ rake install_prereqs

Other Dependencies
------------------
You'll also need to install [MongoDB](http://www.mongodb.org/), since our
application uses it in addition to sqlite. You can install it through your
system package manager, and I suggest that you configure it to start
automatically when you boot up your system, so that you never have to worry
about it again. For Mac, use
[`launchd`](https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/launchd.8.html)
(running `brew info mongodb` will give you some commands you can copy-paste.)
For Linux, you can use [`upstart`](http://upstart.ubuntu.com/), `chkconfig`,
or any other process management tool.

Configuring Your Project
------------------------
We use [`rake`](http://rake.rubyforge.org/) to execute common tasks in our
project. The `rake` tasks are defined in the `rakefile`, or you can run `rake -T`
to view a summary.

Before you run your project, you need to create a sqlite database, create
tables in that database, run database migrations, and populate templates for
CMS templates. Fortunately, `rake` will do all of this for you! Just run:

    $ rake django-admin[syncdb]
    $ rake django-admin[migrate]

If you are running these commands using the [`zsh`](http://www.zsh.org/) shell,
zsh will assume that you are doing
[shell globbing](https://en.wikipedia.org/wiki/Glob_%28programming%29), search for
a file in your directory named `django-adminsyncdb` or `django-adminmigrate`,
and fail. To fix this, just surround the argument with quotation marks, so that
you're running `rake "django-admin[syncdb]"`.

Run Your Project
----------------
edX has two components: Studio, the course authoring system; and the LMS
(learning management system) used by students. These two systems communicate
through the MongoDB database, which stores course information.

To run Studio, run:

    $ rake cms

To run the LMS, run:

    $ rake lms[cms.dev]

Studio runs on port 8001, while LMS runs on port 8000, so you can run both of
these commands simultaneously, using two different terminal windows. To view
Studio, visit `127.0.0.1:8001` in your web browser; to view the LMS, visit
`127.0.0.1:8000`.

There's also an older version of the LMS that saves its information in XML files
in the `data` directory, instead of in Mongo. To run this older version, run:

    $ rake lms

License
-------

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

Documentation
------------

High-level documentation of the code is located in the `doc` subdirectory. Start
with `overview.md` to get an introduction to the architecture of the system.

How to Contribute
-----------------

Contributions are very welcome. The easiest way is to fork this repo, and then
make a pull request from your fork. The first time you make a pull request, you
may be asked to sign a Contributor Agreement.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Mailing List and IRC Channel
----------------------------

You can discuss this code on the [edx-code Google Group](https://groups.google.com/forum/#!forum/edx-code) or in the
`edx-code` IRC channel on Freenode.
