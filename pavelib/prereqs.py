from paver.easy import *
from paver.setuputils import setup
import os
from distutils import sysconfig

import prereqs_cache

setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)

NPM_REGISTRY = "http://registry.npmjs.org/"


@task
def install_prereqs():
    """
       installs ruby, node and python prerequisites
    """

    install_ruby_prereqs()
    install_node_prereqs()
    install_python_prereqs()
    pass


@task
def install_ruby_prereqs():
    """
      installs ruby prereqs
    """
    if prereqs_cache.is_changed('ruby_prereqs', ['Gemfile']):
        sh('bundle install --quiet')
    else:
        print('Ruby requirements unchanged, nothing to install')


@task
def install_node_prereqs():
    """
      installs node prerequisites
    """
    if prereqs_cache.is_changed('npm_prereqs', ['package.json']):
        sh("npm config set registry %s " % (NPM_REGISTRY))
        sh('npm install')
    else:
        print('Node requirements unchanged, nothing to install')


@task
def install_python_prereqs():
    """
      installs python prerequisites
    """
    site_packages_dir = sysconfig.get_python_lib()

    requirements = prereqs_cache.get_files('requirements')

    if prereqs_cache.is_changed('requirements_prereqs', requirements, [site_packages_dir]):
        req_files = ["requirements/edx/pre.txt", "requirements/edx/base.txt", "requirements/edx/post.txt"]
        for req_file in req_files:
            sh("pip install -q -r --exists-action w {req_file}".format(req_file=req_file))

        # requirements/private.txt is used to install our libs as
        # working dirs, or for personal-use tools.
        if os.path.exists("requirements/private.txt"):
            sh('pip install -q -r requirements/private.txt')
    else:
        print('Python requirements unchanged, nothing to install')
