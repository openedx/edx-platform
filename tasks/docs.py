from __future__ import print_function
import sys

from invoke import task
from invoke import run as sh

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


def doc_path(doc_type, allow_default=True):
    """
    Determine the path of the documentation directory based on the document type.
    If the specified path is not one of the valid options, print an error
    message and exit.

    If `allow_default` is False, then require that a type is specified,
    and exit with an error message if it isn't.
    """

    path = DOC_PATHS.get(doc_type)

    if doc_type == 'default' and not allow_default:
        print("You must specify a documentation type using '--type'.  "
              "Valid options are: {options}".format(
                  options=valid_doc_types()))
        sys.exit(2)

    if path is None:
        print("Invalid documentation type '{doc_type}'.  "
              "Valid options are: {options}".format(
                  doc_type=doc_type, options=valid_doc_types()))
        sys.exit(2)
    return path

@task('prereqs.install',
      help={"type": "Type of docs to compile",
            "verbose": "Display verbose output"
      })
def build(type='default', verbose=False):
    """
    Invoke sphinx 'make build' to generate docs.
    """

    sh("cd {dir}; make html quiet={quiet}"
       .format(dir=doc_path(type),
               quiet="false" if verbose else "true"))
