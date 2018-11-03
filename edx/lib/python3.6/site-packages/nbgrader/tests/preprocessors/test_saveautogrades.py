import pytest

from nbformat.v4 import new_notebook, new_output

from ...preprocessors import SaveCells, SaveAutoGrades
from ...api import Gradebook
from ...utils import compute_checksum
from .base import BaseTestPreprocessor
from .. import (
    create_grade_cell, create_grade_and_solution_cell, create_solution_cell)


@pytest.fixture
def preprocessors():
    return (SaveCells(), SaveAutoGrades())


@pytest.fixture
def gradebook(request, db):
    gb = Gradebook(db)
    gb.add_assignment("ps0")
    gb.add_student("bar")

    def fin():
        gb.close()
    request.addfinalizer(fin)

    return gb


@pytest.fixture
def resources(db):
    return {
        "nbgrader": {
            "db_url": db,
            "assignment": "ps0",
            "notebook": "test",
            "student": "bar"
        }
    }


class TestSaveAutoGrades(BaseTestPreprocessor):

    def test_grade_correct_code(self, preprocessors, gradebook, resources):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 1
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_incorrect_code(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        cell.outputs = [new_output('error', ename="NotImplementedError", evalue="", traceback=["error"])]
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

    def test_comment_unchanged_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment("foo", "test", "ps0", "bar")
        assert comment.auto_comment == "No response."

    def test_comment_changed_code(self, preprocessors, gradebook, resources):
        """Is a changed code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment("foo", "test", "ps0", "bar")
        assert comment.auto_comment is None

    def test_comment_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment("foo", "test", "ps0", "bar")
        assert comment.auto_comment == "No response."

    def test_comment_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment("foo", "test", "ps0", "bar")
        assert comment.auto_comment is None

    def test_grade_existing_manual_grade(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

        grade_cell.manual_score = 1
        grade_cell.needs_manual_grade = False
        gradebook.db.commit()

        preprocessors[1].preprocess(nb, resources)

        grade_cell = gradebook.find_grade("foo", "test", "ps0", "bar")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == 1
        assert grade_cell.needs_manual_grade

    def test_grade_existing_auto_comment(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader['checksum'] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        gradebook.add_submission("ps0", "bar")
        preprocessors[1].preprocess(nb, resources)

        comment = gradebook.find_comment("foo", "test", "ps0", "bar")
        assert comment.auto_comment == "No response."

        nb.cells[-1].source = 'goodbye'
        preprocessors[1].preprocess(nb, resources)

        gradebook.db.refresh(comment)
        assert comment.auto_comment is None
