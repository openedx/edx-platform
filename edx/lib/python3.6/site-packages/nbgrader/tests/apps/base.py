import os
import shutil
import pytest

from nbformat import write as write_nb
from nbformat.v4 import new_notebook

from ...utils import remove


@pytest.mark.usefixtures("temp_cwd")
class BaseTestApp(object):

    def _empty_notebook(self, path, kernel=None):
        nb = new_notebook()
        if kernel is not None:
            nb.metadata.kernelspec = {
                "display_name": "kernel",
                "language": kernel,
                "name": kernel
            }

        full_dest = os.path.abspath(path)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        if os.path.exists(full_dest):
            remove(full_dest)
        with open(full_dest, 'w') as f:
            write_nb(nb, f, 4)

    def _copy_file(self, src, dest):
        full_src = os.path.join(os.path.dirname(__file__), src)
        full_dest = os.path.abspath(dest)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        if os.path.exists(full_dest):
            remove(full_dest)
        shutil.copy(full_src, full_dest)

    def _move_file(self, src, dest):
        full_src = os.path.abspath(src)
        full_dest = os.path.abspath(dest)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        if os.path.exists(full_dest):
            remove(full_dest)
        shutil.move(full_src, full_dest)

    def _make_file(self, path, contents=""):
        full_dest = os.path.abspath(path)
        if not os.path.exists(os.path.dirname(full_dest)):
            os.makedirs(os.path.dirname(full_dest))
        if os.path.exists(full_dest):
            remove(full_dest)
        with open(path, "w") as fh:
            fh.write(contents)

    def _get_permissions(self, filename):
        return oct(os.stat(filename).st_mode)[-3:]

    def _file_contents(self, path):
        with open(path, "r") as fh:
            contents = fh.read()
        return contents
