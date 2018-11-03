import json
import pytest

from nbformat import validate
from nbformat.v4 import new_notebook

from ...preprocessors import SaveCells, OverwriteKernelspec
from ...api import Gradebook
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessors():
    return (SaveCells(), OverwriteKernelspec())


@pytest.fixture
def gradebook(request, db):
    gb = Gradebook(db)
    gb.add_assignment("ps0")

    def fin():
        gb.close()
    request.addfinalizer(fin)

    return gb


@pytest.fixture
def resources(db, gradebook):
    return {
        "nbgrader": {
            "db_url": db,
            "assignment": "ps0",
            "notebook": "test"
        }
    }


class TestOverwriteKernelSpec(BaseTestPreprocessor):

    def test_overwrite_kernelspec(self, preprocessors, resources, gradebook):
        kernelspec = dict(
            display_name='blarg',
            name='python3',
            language='python',
        )

        nb = new_notebook()
        nb.metadata['kernelspec'] = kernelspec
        nb, resources = preprocessors[0].preprocess(nb, resources)

        nb.metadata['kernelspec'] = {}
        nb, resources = preprocessors[1].preprocess(nb, resources)

        validate(nb)
        notebook = gradebook.find_notebook("test", "ps0")
        assert nb.metadata['kernelspec'] == kernelspec
        assert json.loads(notebook.kernelspec) == kernelspec
