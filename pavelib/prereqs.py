from paver.easy import *
from paver.setuputils import setup
import os

setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)


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
    sh('bundle install --quiet')


@task
def install_node_prereqs():
    """
      installs node prerequisites
    """
    sh('npm install')


@task
def install_python_prereqs():
    """
      installs python prerequisites
    """
    sh('pip install -q --exists-action w -r requirements/edx/pre.txt')
    sh('pip install -q --exists-action w -r requirements/edx/base.txt')
    sh('pip install -q --exists-action w -r requirements/edx/post.txt')
    # requirements/private.txt is used to install our libs as
    # working dirs, or for personal-use tools.
    if os.path.exists("requirements/private.txt"):
        sh('pip install -q -r requirements/private.txt')
