"""
Install Python, Ruby, and Node prerequisites.
"""

import os
import hashlib
from distutils import sysconfig
from paver.easy import *
from .utils.envs import Env


PREREQS_MD5_DIR = os.getenv('PREREQ_CACHE_DIR', Env.REPO_ROOT / '.prereqs_cache')
NPM_REGISTRY = "http://registry.npmjs.org/"
PYTHON_REQ_FILES = [
    'requirements/edx/pre.txt',
    'requirements/edx/base.txt',
    'requirements/edx/post.txt'
]


def read_in_chunks(infile, chunk_size=1024 * 64):
    """
    Yield a chunk of size `chunksize` from `infile` (a file handle).
    """
    chunk = infile.read(chunk_size)
    while chunk:
        yield chunk
        chunk = infile.read(chunk_size)


def compute_fingerprint(path_list):
    """
    Hash the contents of all the files and directories in `path_list`.
    Returns the hex digest.
    """

    hasher = hashlib.sha1()

    for path in path_list:

        # For directories, create a hash based on the filenames in the directory
        if os.path.isdir(path):
            for _, _, filenames in os.walk(path):
                for name in filenames:
                    hasher.update(name)

        # For files, hash the contents of the file
        if os.path.isfile(path):
            with open(path, "rb") as file_handle:
                for chunk in read_in_chunks(file_handle):
                    hasher.update(chunk)

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
    cache_file_path = os.path.join(PREREQS_MD5_DIR, "{}.sha1".format(cache_filename))
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
            os.makedirs(PREREQS_MD5_DIR)
        except OSError:
            if not os.path.isdir(PREREQS_MD5_DIR):
                raise

        with open(cache_file_path, "w") as cache_file:
            cache_file.write(new_hash)

    else:
        print '{cache} unchanged, skipping...'.format(cache=cache_name)


def install_ruby_prereqs():
    """
    Installs Ruby prereqs
    """
    sh('bundle install --quiet')


def install_node_prereqs():
    """
    Installs Node prerequisites
    """
    sh("npm config set registry {}".format(NPM_REGISTRY))
    sh('npm install')


def install_python_prereqs():
    """
    Installs Python prerequisites
    """
    for req_file in PYTHON_REQ_FILES:
        sh("pip install -q --exists-action w -r {req_file}".format(req_file=req_file))


@task
def install_prereqs():
    """
    Installs Ruby, Node and Python prerequisites
    """
    prereq_cache("Ruby prereqs", ["Gemfile"], install_ruby_prereqs)
    prereq_cache("Node prereqs", ["package.json"], install_node_prereqs)
    prereq_cache("Python prereqs", PYTHON_REQ_FILES + [sysconfig.get_python_lib()], install_python_prereqs)
