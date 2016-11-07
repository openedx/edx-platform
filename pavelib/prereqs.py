"""
Install Python and Node prerequisites.
"""

from distutils import sysconfig
import hashlib
import os
import re
import sys

from paver.easy import sh, task

from pavelib.utils.passthrough_opts import PassthroughTask
from .utils.envs import Env
from .utils.timer import timed


PREREQS_STATE_DIR = os.getenv('PREREQ_CACHE_DIR', Env.REPO_ROOT / '.prereqs_cache')
NPM_REGISTRY = "http://registry.npmjs.org/"
NO_PREREQ_MESSAGE = "NO_PREREQ_INSTALL is set, not installing prereqs"
COVERAGE_REQ_FILE = 'requirements/edx/coverage.txt'

# If you make any changes to this list you also need to make
# a corresponding change to circle.yml, which is how the python
# prerequisites are installed for builds on circleci.com
PYTHON_REQ_FILES = [
    'requirements/edx/pre.txt',
    'requirements/edx/github.txt',
    'requirements/edx/local.txt',
    'requirements/edx/base.txt',
    'requirements/edx/paver.txt',
    'requirements/edx/post.txt',
]

PYTHON_SANDBOX_REQ_FILES = [
    'requirements/edx-sandbox/base.txt',
    'requirements/edx-sandbox/local.txt',
    'requirements/edx-sandbox/post.txt',
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


def create_prereqs_cache_dir():
    """Create the directory for storing the hashes, if it doesn't exist already."""
    try:
        os.makedirs(PREREQS_STATE_DIR)
    except OSError:
        if not os.path.isdir(PREREQS_STATE_DIR):
            raise


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
        create_prereqs_cache_dir()
        with open(cache_file_path, "w") as cache_file:
            # Since the pip requirement files are modified during the install
            # process, we need to store the hash generated AFTER the installation
            post_install_hash = compute_fingerprint(paths)
            cache_file.write(post_install_hash)
    else:
        print '{cache} unchanged, skipping...'.format(cache=cache_name)


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
    pip_sync_req_files(PYTHON_REQ_FILES)


def pip_install_req_file(req_file):
    """Pip install the requirements file."""
    pip_cmd = 'pip install -q --disable-pip-version-check --exists-action w'
    sh("{pip_cmd} -r {req_file}".format(pip_cmd=pip_cmd, req_file=req_file))

def pip_sync_req_files(req_files):
    """Use pip-sync to install requirements files."""
    sh("pip-sync --phased {}".format(" ".join(req_files)))

def pip_compile_req_files(files, options):
    """Use pip-compile to install requirements files."""
    command = ["pip-compile", "--phased"]
    command.extend(options)
    command.extend(files)
    sh(command)


@PassthroughTask
@timed
def compile_python_req_files(passthrough_options):
    """
    Builds a consistent set of pinned requirement files using pip-compile.
    """
    pip_compile_req_files(
        files=[outfile.replace(".txt", ".in") for outfile in PYTHON_REQ_FILES],
        options=passthrough_options
    )
    pip_compile_req_files(
        files=[outfile.replace(".txt", ".in") for outfile in PYTHON_SANDBOX_REQ_FILES],
        options=passthrough_options
    )


@task
@timed
def install_node_prereqs():
    """
    Installs Node prerequisites
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    prereq_cache("Node prereqs", ["package.json"], node_prereqs_installation)


@task
@timed
def install_coverage_prereqs():
    """ Install python prereqs for measuring coverage. """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return
    pip_install_req_file(COVERAGE_REQ_FILE)


@task
@timed
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
@timed
def install_prereqs():
    """
    Installs Node and Python prerequisites
    """
    if no_prereq_install():
        print NO_PREREQ_MESSAGE
        return

    install_node_prereqs()
    install_python_prereqs()
