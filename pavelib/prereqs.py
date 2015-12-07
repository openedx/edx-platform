"""
Install Python, Ruby, and Node prerequisites.
"""

from distutils import sysconfig
import hashlib
import os

from paver.easy import sh, task

from .utils.envs import Env
import sys


PREREQS_STATE_DIR = os.getenv('PREREQ_CACHE_DIR', Env.REPO_ROOT / '.prereqs_cache')
NPM_REGISTRY = "http://registry.npmjs.org/"
NO_PREREQ_MESSAGE = "NO_PREREQ_INSTALL is set, not installing prereqs"

# If you make any changes to this list you also need to make
# a corresponding change to circle.yml, which is how the python
# prerequisites are installed for builds on circleci.com
PYTHON_REQ_FILES = [
    'requirements/edx/pre.txt',
    'requirements/edx/github.txt',
    'requirements/edx/local.txt',
    'requirements/edx/base.txt',
    'requirements/edx/post.txt',
]

# Developers can have private requirements, for local copies of github repos,
# or favorite debugging tools, etc.
PRIVATE_REQS = 'requirements/private.txt'
if os.path.exists(PRIVATE_REQS):
    PYTHON_REQ_FILES.append(PRIVATE_REQS)


def no_prereq_install():
    """
    Determine if NO_PREREQ_INSTALL should be truthy or falsy.
    """
    vals = {
        '0': False,
        '1': True,
        'true': True,
        'false': False,
    }

    val = os.environ.get("NO_PREREQ_INSTALL", 'False').lower()

    try:
        return vals[val]
    except KeyError:
        return False


def compute_fingerprint(path_list):
    """
    Hash the contents of all the files and directories in `path_list`.
    Returns the hex digest.
    """

    hasher = hashlib.sha1()

    for path_item in path_list:

        # For directories, create a hash based on the modification times
        # of first-level subdirectories
        if os.path.isdir(path_item):
            for dirname in sorted(os.listdir(path_item)):
                path_name = os.path.join(path_item, dirname)
                if os.path.isdir(path_name):
                    hasher.update(str(os.stat(path_name).st_mtime))

        # For files, hash the contents of the file
        if os.path.isfile(path_item):
            with open(path_item, "rb") as file_handle:
                hasher.update(file_handle.read())

    return hasher.hexdigest()


def prereq_cache(cache_name, paths, install_func):
    """
    Conditionally execute `install_func()` only if the files/directories
    specified by `paths` have changed.

    If the code executes successfully (no exceptions are thrown), the cache
    is updated with the new hash.
    """
    # Retrieve the old hash
    cache_filename = cache_name.replace(" ", "_")
    cache_file_path = os.path.join(PREREQS_STATE_DIR, "{}.sha1".format(cache_filename))
    old_hash = None
    if os.path.isfile(cache_file_path):
        with open(cache_file_path) as cache_file:
            old_hash = cache_file.read()

    # Compare the old hash to the new hash
    # If they do not match (either the cache hasn't been created, or the files have changed),
    # then execute the code within the block.
    new_hash = compute_fingerprint(paths)
    if new_hash != old_hash:
        install_func()

        # Update the cache with the new hash
        # If the code executed within the context fails (throws an exception),
        # then this step won't get executed.
        try:
            os.makedirs(PREREQS_STATE_DIR)
        except OSError:
            if not os.path.isdir(PREREQS_STATE_DIR):
                raise

        with open(cache_file_path, "w") as cache_file:
            # Since the pip requirement files are modified during the install
            # process, we need to store the hash generated AFTER the installation
            post_install_hash = compute_fingerprint(paths)
            cache_file.write(post_install_hash)
    else:
        print '{cache} unchanged, skipping...'.format(cache=cache_name)


def ruby_prereqs_installation():
    """
    Installs Ruby prereqs
    """
    sh('bundle install --quiet')


def node_prereqs_installation():
    """
    Configures npm and installs Node prerequisites
    """
    sh("test `npm config get registry` = \"{reg}\" || "
       "(echo setting registry; npm config set registry"
       " {reg})".format(reg=NPM_REGISTRY))
    sh('npm install')


def python_prereqs_installation():
    """
    Installs Python prerequisites
    """
    for req_file in PYTHON_REQ_FILES:
        sh("pip install -q --disable-pip-version-check --exists-action w -r {req_file}".format(req_file=req_file))


@task
def install_ruby_prereqs():
    """
    Installs Ruby prereqs
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    prereq_cache("Ruby prereqs", ["Gemfile"], ruby_prereqs_installation)


@task
def install_node_prereqs():
    """
    Installs Node prerequisites
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    prereq_cache("Node prereqs", ["package.json"], node_prereqs_installation)


@task
def uninstall_python_packages():
    """
    Uninstall Python packages that need explicit uninstallation.

    Some Python packages that we no longer want need to be explicitly
    uninstalled, notably, South.  Some other packages were once installed in
    ways that were resistant to being upgraded, like edxval.  Also uninstall
    them.

    """
    # So that we don't constantly uninstall things, use a version number of the
    # uninstallation needs.  Check it, and skip this if we're up to date.
    expected_version = 2
    state_file_path = os.path.join(PREREQS_STATE_DIR, "python_uninstall_version.txt")
    if os.path.isfile(state_file_path):
        with open(state_file_path) as state_file:
            version = int(state_file.read())
        if version == expected_version:
            return

    # Run pip to find the packages we need to get rid of.  Believe it or not,
    # edx-val is installed in a way that it is present twice, so we have a loop
    # to really really get rid of it.
    for _ in range(3):
        uninstalled = False
        frozen = sh("pip freeze", capture=True).splitlines()

        # Uninstall South
        if any(line.startswith("South") for line in frozen):
            sh("pip uninstall --disable-pip-version-check -y South")
            uninstalled = True

        # Uninstall edx-val
        if any("edxval" in line for line in frozen):
            sh("pip uninstall --disable-pip-version-check -y edxval")
            uninstalled = True

        # Uninstall django-storages
        if any("django-storages==" in line for line in frozen):
            sh("pip uninstall --disable-pip-version-check -y django-storages")
            uninstalled = True

        if not uninstalled:
            break
    else:
        # We tried three times and didn't manage to get rid of the pests.
        print "Couldn't uninstall unwanted Python packages!"
        return

    # Write our version.
    with open(state_file_path, "w") as state_file:
        state_file.write(str(expected_version))


@task
def install_python_prereqs():
    """
    Installs Python prerequisites.
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    # Include all of the requirements files in the fingerprint.
    files_to_fingerprint = list(PYTHON_REQ_FILES)

    # Also fingerprint the directories where packages get installed:
    # ("/edx/app/edxapp/venvs/edxapp/lib/python2.7/site-packages")
    files_to_fingerprint.append(sysconfig.get_python_lib())

    # In a virtualenv, "-e installs" get put in a src directory.
    src_dir = os.path.join(sys.prefix, "src")
    if os.path.isdir(src_dir):
        files_to_fingerprint.append(src_dir)

    # Also fingerprint this source file, so that if the logic for installations
    # changes, we will redo the installation.
    this_file = __file__
    if this_file.endswith(".pyc"):
        this_file = this_file[:-1]      # use the .py file instead of the .pyc
    files_to_fingerprint.append(this_file)

    prereq_cache("Python prereqs", files_to_fingerprint, python_prereqs_installation)


@task
def install_prereqs():
    """
    Installs Ruby, Node and Python prerequisites
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    install_ruby_prereqs()
    install_node_prereqs()
    uninstall_python_packages()
    install_python_prereqs()
