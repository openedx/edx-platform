from __future__ import print_function
import sys
from paver.easy import *


DOC_PATHS = {
    "dev": "docs/en_us/developers",
    "author": "docs/en_us/course_authors",
    "data": "docs/en_us/data",
    "default": "docs/en_us"
}


def valid_doc_types():
    """
    Return a comma-separated string of valid doc types.
    """
    return ", ".join(DOC_PATHS.keys())


def doc_path(options, allow_default=True):
    """
    Parse `options` (from the Paver task args) to determine the path
    to the documentation directory.
    If the specified path is not one of the valid options, print an error
    message and exit.

    If `allow_default` is False, then require that a type is specified,
    and exit with an error message if it isn't.
    """
    doc_type = getattr(options, 'type', 'default')
    path = DOC_PATHS.get(doc_type)

    if doc_type == 'default' and not allow_default:
        print(
            "You must specify a documentation type using '--type'.  "
            "Valid options are: {options}".format(
                options=valid_doc_types()
            )
        )
        sys.exit(1)

    if path is None:
        print(
            "Invalid documentation type '{doc_type}'.  "
            "Valid options are: {options}".format(
                doc_type=doc_type, options=valid_doc_types()
            )
        )
        sys.exit(1)

    else:
        return path


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("type=", "t", "Type of docs to compile"),
    ("verbose", "v", "Display verbose output"),
])
def build_docs(options):
    """
    Invoke sphinx 'make build' to generate docs.
    """
    verbose = getattr(options, 'verbose', False)

    cmd = "cd {dir}; make html quiet={quiet}".format(
        dir=doc_path(options),
        quiet="false" if verbose else "true"
    )

    sh(cmd)
