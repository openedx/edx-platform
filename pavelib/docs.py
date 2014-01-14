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

    paths = {
        "dev": "docs/developers",
        "author": "docs/course_authors",
        "data": "docs/data",
    }

    path = paths.get(type, "docs/developers")

    sh("cd {dir}; make html quiet={quiet}".format(
        dir=path, quiet="false" if verbose else "true")
       )


@task
@cmdopts([
    ("type=", "t", "Type of docs to show"),
])
def show_docs(options):
    """
       Show docs in browser
    """

    type = getattr(options, 'type', 'docs')

    paths = {
        "dev": "docs/developers",
        "author": "docs/course_authors",
        "data": "docs/data",
    }

    path = paths.get(type, "docs/developers")

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
