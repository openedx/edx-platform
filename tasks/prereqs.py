"""
Install Python, Ruby, and Node prerequisites.
"""

import os
import hashlib
from distutils import sysconfig
from invoke import Collection
from invoke import task
from invoke import run as sh
from path import path

from .utils.envs import Env

ns = Collection()


PREREQS_MD5_DIR = os.getenv('PREREQ_CACHE_DIR', Env.REPO_ROOT / '.prereqs_cache')
PREREQS_MD5_DIR = path(PREREQS_MD5_DIR)
NPM_REGISTRY = "http://registry.npmjs.org/"
PYTHON_REQ_FILES = [
    path('requirements/edx/pre.txt'),
    path('requirements/edx/github.txt'),
    path('requirements/edx/local.txt'),
    path('requirements/edx/base.txt'),
    path('requirements/edx/post.txt'),
]

# Developers can have private requirements, for local copies of github repos,
# or favorite debugging tools, etc.
PRIVATE_REQS = path('requirements/private.txt')
if os.path.exists(PRIVATE_REQS):
    PYTHON_REQ_FILES.append(PRIVATE_REQS)


def compute_fingerprint(path_list):
    """
    Hash the contents of all the files and directories in `path_list`.
    Returns the hex digest.
    """

    hasher = hashlib.sha1()

    for p in path_list:
        p = path(p)

        # For directories, create a hash based on the modification times
        # of first-level subdirectories
        if p.isdir():
            for dir in sorted(p.dirs()):
                mtime = dir.stat().st_mtime
                hasher.update(str(mtime))

        # For files, hash the contents of the file
        if p.isfile():
            hasher.update(p.text())

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
    cache_file_path = PREREQS_MD5_DIR / (cache_filename + ".sha1")
    old_hash = None
    if cache_file_path.isfile():
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
        PREREQS_MD5_DIR.makedirs_p()

        # recalculate hash
        new_hash = compute_fingerprint(paths)
        # write to cache file
        cache_file_path.write_text(new_hash)

    else:
        print('{cache} unchanged, skipping...'.format(cache=cache_name))


@task
def show_cache_hashes():
    """
    Show SHA1 hashes for prereq caches
    """
    caches = ("Ruby prereqs", "Node prereqs", "Python prereqs")
    for cache in caches:
        cache_filename = cache.replace(" ", "_")
        cache_file_path = PREREQS_MD5_DIR / (cache_filename + ".sha1")
        if cache_file_path.isfile():
            with open(cache_file_path) as cache_file:
                prereq_hash = cache_file.read()
            print("{cache}: {hash}".format(cache=cache, hash=prereq_hash))


@task
def flush_cache_hashes():
    """
    Flush prereq caches
    """
    if not PREREQS_MD5_DIR.exists():
        return
    for f in PREREQS_MD5_DIR.files():
        f.remove()

@task
def install_ruby_prereqs():
    """
    Installs Ruby prereqs
    """
    sh('bundle install --quiet')


@task
def install_node_prereqs():
    """
    Installs Node prerequisites
    """
    sh("npm config set registry {}".format(NPM_REGISTRY))
    sh('npm install')


@task
def install_python_prereqs():
    """
    Installs Python prerequisites
    """
    for req_file in PYTHON_REQ_FILES:
        print(req_file)
        sh("pip install --exists-action w -r {req_file}".format(req_file=req_file), hide='stdout')


@task(default=True)
def install(**kwargs):
    """
    Installs Ruby, Node and Python prerequisites
    """
    if os.environ.get("NO_PREREQ_INSTALL", False):
        return

    prereq_cache("Ruby prereqs", ["Gemfile"], install_ruby_prereqs)
    prereq_cache("Node prereqs", ["package.json"], install_node_prereqs)
    prereq_cache("Python prereqs", PYTHON_REQ_FILES + [sysconfig.get_python_lib()], install_python_prereqs)


install_ns = Collection('install')
install_ns.add_task(install_ruby_prereqs, 'ruby')
install_ns.add_task(install_node_prereqs, 'node')
install_ns.add_task(install_python_prereqs, 'python')
install_ns.add_task(install, 'all', default=True)
ns.add_collection(install_ns)

cache_ns = Collection('cache')
cache_ns.add_task(show_cache_hashes, "show", default=True)
cache_ns.add_task(flush_cache_hashes, "flush")
ns.add_collection(cache_ns)

ns.default = "install.all"
