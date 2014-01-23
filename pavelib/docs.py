from paver.easy import *
from pavelib import assets
import webbrowser


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

    webbrowser.open('file://{root}/{path}/build/html/index.html'.format(
                    root=assets.REPO_ROOT, path=path)
                    )


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
