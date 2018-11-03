import pytest
import tempfile
import os
import shutil


@pytest.fixture
def db(request):
    path = tempfile.mkdtemp()
    dbpath = os.path.join(path, "nbgrader_test.db")

    def fin():
        shutil.rmtree(path)
    request.addfinalizer(fin)

    return "sqlite:///" + dbpath
