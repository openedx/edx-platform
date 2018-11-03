import pytest
import itertools
import os

from ...preprocessors import LockCells
from .base import BaseTestPreprocessor
from .. import create_code_cell


@pytest.fixture
def preprocessor():
    return LockCells()


class TestLockCells(BaseTestPreprocessor):

    @staticmethod
    def deletable(cell):
        return cell.metadata.get('deletable', True)

    @staticmethod
    def editable(cell):
        return cell.metadata.get('editable', True)

    def test_solution_cell_undeletable(self, preprocessor):
        """Do solution cells become undeletable?"""
        preprocessor.lock_solution_cells = True
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)
        assert self.editable(cell)

    def test_solution_cell_unchanged(self, preprocessor):
        """Do solution cells remain unchanged?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)
        assert self.editable(cell)

    def test_locked_cell_undeletable(self, preprocessor):
        """Do locked cells become undeletable?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = True
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['locked'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)
        assert not self.editable(cell)

    def test_grade_cell_undeletable(self, preprocessor):
        """Do grade cells become undeletable?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = True
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)
        assert not self.editable(cell)

    def test_grade_cell_unchanged(self, preprocessor):
        """Do grade cells remain unchanged?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)
        assert self.editable(cell)

    def test_grade_and_solution_cell_undeletable(self, preprocessor):
        """Do grade and solution cells become undeletable?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = True
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)
        assert self.editable(cell)

    def test_grade_and_solution_cell_unchanged(self, preprocessor):
        """Do grade and solution cells remain unchanged?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)
        assert self.editable(cell)

    def test_cell_undeletable(self, preprocessor):
        """Do normal cells become undeletable?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = True
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)
        assert not self.editable(cell)

    def test_cell_unchanged(self, preprocessor):
        """Do normal cells remain unchanged?"""
        preprocessor.lock_solution_cells = False
        preprocessor.lock_grade_cells = False
        preprocessor.lock_all_cells = False
        preprocessor.lock_readonly_cells = False
        cell = create_code_cell()
        cell.metadata['nbgrader'] = {}
        assert self.deletable(cell)
        assert self.editable(cell)
        new_cell = preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)
        assert self.editable(cell)

    @pytest.mark.parametrize(
        "lock_solution_cells, lock_grade_cells, lock_all_cells, lock_readonly_cells",
        list(itertools.product([True, False], [True, False], [True, False], [True, False]))
    )
    def test_preprocess_nb(self, preprocessor, lock_solution_cells, lock_grade_cells, lock_all_cells, lock_readonly_cells):
        """Is the test notebook processed without error?"""
        preprocessor.lock_solution_cells = lock_solution_cells
        preprocessor.lock_grade_cells = lock_grade_cells
        preprocessor.lock_all_cells = lock_all_cells
        preprocessor.lock_readonly_cells = lock_readonly_cells
        preprocessor.preprocess(self._read_nb(os.path.join("files", "test.ipynb")), {})
