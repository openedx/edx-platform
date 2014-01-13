from paver.easy import *
from paver.setuputils import setup
from pavelib import assets
import webbrowser

setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)


@task
@cmdopts([
    ("type=", "t", "Type of docs to compile"),
    ("verbose", "v", "Display verbose output"),
])
def build_docs(options):
    """
       Invoke sphinx 'make build' to generate docs.
    """

    type = getattr(options, 'type', 'docs')
    verbose = getattr(options, 'verbose', True)

    if type == 'dev':
        path = "docs/developers"
    elif type == 'author':
        path = "docs/course_authors"
    elif type == 'data':
        path = "docs/data"
    else:
        path = "docs/developers"

    if verbose:
        sh('cd %s;' % (path) + 'make html quiet=false')
    else:
        sh('cd %s;' % (path) + 'make html quiet=true')


@task
@cmdopts([
    ("type=", "t", "Type of docs to show"),
])
def show_docs(options):
    """
       Show docs in browser
    """

    type = getattr(options, 'type', 'docs')

    if type == 'dev':
        path = "docs/developers"
    elif type == 'author':
        path = "docs/course_authors"
    elif type == 'data':
        path = "docs/data"
    else:
        path = "docs/developers"

    webbrowser.open('file://%s/%s' % (assets.REPO_ROOT, path) + '/build/html/index.html')


@task
@cmdopts([
    ("type=", "t", "Type of docs to compile"),
    ("verbose", "v", "Display verbose output"),
])
def doc(options):
    """
       Build docs and show them in browser
    """

    build_docs(options)
    show_docs(options)
