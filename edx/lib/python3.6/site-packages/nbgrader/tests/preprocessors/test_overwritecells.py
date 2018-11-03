import pytest

from nbformat.v4 import new_notebook

from ...preprocessors import SaveCells, OverwriteCells
from ...api import Gradebook
from ...utils import compute_checksum
from .base import BaseTestPreprocessor
from .. import (
    create_grade_cell, create_solution_cell, create_grade_and_solution_cell,
    create_locked_cell)


@pytest.fixture
def preprocessors():
    return (SaveCells(), OverwriteCells())


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


class TestOverwriteCells(BaseTestPreprocessor):

    def test_overwrite_points(self, preprocessors, resources):
        """Are points overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["points"] = 2
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["points"] == 1

    def test_overwrite_grade_source(self, preprocessors, resources):
        """Is the source overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello"

    def test_overwrite_locked_source_code(self, preprocessors, resources):
        """Is the source overwritten for locked code cells?"""
        cell = create_locked_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello"

    def test_overwrite_locked_source_markdown(self, preprocessors, resources):
        """Is the source overwritten for locked markdown cells?"""
        cell = create_locked_cell("hello", "markdown", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello"

    def test_dont_overwrite_grade_and_solution_source(self, preprocessors, resources):
        """Is the source not overwritten for grade+solution cells?"""
        cell = create_grade_and_solution_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello!"

    def test_dont_overwrite_solution_source(self, preprocessors, resources):
        """Is the source not overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.source = "hello!"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.source == "hello!"

    def test_overwrite_grade_cell_type(self, preprocessors, resources):
        """Is the cell type overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.cell_type = "markdown"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.cell_type == "code"

    def test_overwrite_solution_cell_type(self, preprocessors, resources):
        """Is the cell type overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.cell_type = "markdown"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.cell_type == "code"

    def test_overwrite_locked_cell_type(self, preprocessors, resources):
        """Is the cell type overwritten for locked cells?"""
        cell = create_locked_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.cell_type = "markdown"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.cell_type == "code"

    def test_overwrite_grade_checksum(self, preprocessors, resources):
        """Is the checksum overwritten for grade cells?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["checksum"] == compute_checksum(cell)

    def test_overwrite_solution_checksum(self, preprocessors, resources):
        """Is the checksum overwritten for solution cells?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["checksum"] == compute_checksum(cell)

    def test_overwrite_locked_checksum(self, preprocessors, resources):
        """Is the checksum overwritten for locked cells?"""
        cell = create_locked_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)

        cell.metadata.nbgrader["checksum"] = "1234"
        nb, resources = preprocessors[1].preprocess(nb, resources)

        assert cell.metadata.nbgrader["checksum"] == compute_checksum(cell)

    def test_nonexistant_grade_id(self, preprocessors, resources):
        """Are cells not in the database ignored?"""
        cell = create_grade_cell("", "code", "", 1)
        cell.metadata.nbgrader['grade'] = False
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)
        nb, resources = preprocessors[1].preprocess(nb, resources)
        assert 'grade_id' not in cell.metadata.nbgrader

        cell = create_grade_cell("", "code", "foo", 1)
        cell.metadata.nbgrader['grade'] = False
        nb = new_notebook()
        nb.cells.append(cell)
        nb, resources = preprocessors[0].preprocess(nb, resources)
        nb, resources = preprocessors[1].preprocess(nb, resources)
        assert 'grade_id' not in cell.metadata.nbgrader

