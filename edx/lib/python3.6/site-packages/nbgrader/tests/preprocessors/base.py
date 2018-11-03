import os

from nbformat import current_nbformat, read
from ...nbgraderformat import read as read_nb


class BaseTestPreprocessor(object):

    def _read_nb(self, filename, validate=True):
        fullpath = os.path.join(os.path.dirname(__file__), filename)
        with open(fullpath, "r") as fh:
            if validate:
                nb = read_nb(fh, as_version=current_nbformat)
            else:
                nb = read(fh, as_version=current_nbformat)
        return nb
