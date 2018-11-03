import pytest

from ...preprocessors import ComputeChecksums
from ...utils import compute_checksum
from .base import BaseTestPreprocessor
from .. import (
    create_code_cell, create_text_cell,
    create_grade_cell, create_solution_cell, create_locked_cell)


@pytest.fixture
def preprocessor():
    pp = ComputeChecksums()
    pp.comment_index = 0
    return pp


class TestComputeChecksums(BaseTestPreprocessor):

    def test_code_cell_no_checksum(self, preprocessor):
        """Test that no checksum is computed for a regular code cell"""
        cell, _ = preprocessor.preprocess_cell(
            create_code_cell(), {}, 0)
        assert "nbgrader" not in cell.metadata or "checksum" not in cell.metadata.nbgrader

    def test_text_cell_no_checksum(self, preprocessor):
        """Test that no checksum is computed for a regular text cell"""
        cell, _ = preprocessor.preprocess_cell(
            create_text_cell(), {}, 0)
        assert "nbgrader" not in cell.metadata or "checksum" not in cell.metadata.nbgrader

    def test_checksum_grade_cell_type(self, preprocessor):
        """Test that the checksum is computed for grade cells of different cell types"""
        cell1 = create_grade_cell("", "code", "foo", 1)
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_grade_cell("", "markdown", "foo", 1)
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_solution_cell_type(self, preprocessor):
        """Test that the checksum is computed for solution cells of different cell types"""
        cell1 = create_solution_cell("", "code", "foo")
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_solution_cell("", "markdown", "foo")
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_locked_cell_type(self, preprocessor):
        """Test that the checksum is computed for locked cells"""
        cell1 = create_locked_cell("", "code", "foo")
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_locked_cell("", "markdown", "foo")
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_points(self, preprocessor):
        """Test that the checksum is computed for grade cells with different points"""
        cell1 = create_grade_cell("", "code", "foo", 1)
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_grade_cell("", "code", "foo", 2)
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_grade_id(self, preprocessor):
        """Test that the checksum is computed for grade cells with different ids"""
        cell1 = create_grade_cell("", "code", "foo", 1)
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_grade_cell("", "code", "bar", 1)
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_grade_source(self, preprocessor):
        """Test that the checksum is computed for grade cells with different sources"""
        cell1 = create_grade_cell("a", "code", "foo", 1)
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_grade_cell("b", "code", "foo", 1)
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_solution_source(self, preprocessor):
        """Test that the checksum is computed for solution cells with different sources"""
        cell1 = create_solution_cell("a", "code", "foo")
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_solution_cell("b", "code", "foo")
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_grade_and_solution(self, preprocessor):
        """Test that a checksum is created for grade cells that are also solution cells"""
        cell1 = create_grade_cell("", "markdown", "foo", 1)
        cell1 = preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = create_grade_cell("", "markdown", "foo", 1)
        cell2.metadata.nbgrader["solution"] = True
        cell2 = preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"] == compute_checksum(cell1)
        assert cell2.metadata.nbgrader["checksum"] == compute_checksum(cell2)
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]
