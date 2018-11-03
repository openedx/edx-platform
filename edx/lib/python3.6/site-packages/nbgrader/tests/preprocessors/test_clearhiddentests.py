import os
import pytest

from textwrap import dedent
from traitlets.config import Config

from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell
from ...preprocessors import ClearHiddenTests


@pytest.fixture
def preprocessor():
    return ClearHiddenTests()


class TestClearHiddenTests(BaseTestPreprocessor):

    def test_remove_hidden_test_region_code(self, preprocessor):
        """Are hidden test regions in code cells correctly replaced?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN HIDDEN TESTS
            assert True
            ### END HIDDEN TESTS
            """
        ).strip()
        removed_test = preprocessor._remove_hidden_test_region(cell)
        assert removed_test
        assert cell.source == "assert True"

    def test_remove_hidden_test_region_text(self, preprocessor):
        """Are solution regions in text cells correctly replaced?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN HIDDEN TESTS
            this is a test!
            ### END HIDDEN TESTS
            """
        ).strip()
        removed_test = preprocessor._remove_hidden_test_region(cell)
        assert removed_test
        assert cell.source == "something something"

    def test_remove_hidded_test_region_no_end(self, preprocessor):
        """Is an error thrown when there is no end hidden test statement?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN HIDDEN TESTS
            this is a test!
            """
        ).strip()

        with pytest.raises(RuntimeError):
            preprocessor._remove_hidden_test_region(cell)

    def test_remove_hidden_test_region_nested_solution(self, preprocessor):
        """Is an error thrown when there are nested hidden test statements?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN HIDDEN TESTS
            ### BEGIN HIDDEN TESTS
            this is a test!
            """
        ).strip()

        with pytest.raises(RuntimeError):
            preprocessor._remove_hidden_test_region(cell)

    def test_preprocess_code_cell_hidden_test_region(self, preprocessor):
        """Is an error thrown when there is a hidden test region but it's not a grade cell?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN HIDDEN TESTS
            assert True
            ### END HIDDEN TESTS
            """
        ).strip()
        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

    def test_preprocess_code_grade_cell_hidden_test_region(self, preprocessor):
        """Is a code grade cell correctly cleared when there is a hidden test region?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN HIDDEN TESTS
            assert True
            ### END HIDDEN TESTS
            """
        ).strip()
        cell.metadata['nbgrader'] = dict(grade=True)
        resources = dict()
        cell = preprocessor.preprocess_cell(cell, resources, 1)[0]

        assert cell.source == "assert True"
        assert cell.metadata.nbgrader['grade']

    def test_preprocess_text_grade_cell_hidden_test_region(self, preprocessor):
        """Is a text grade cell correctly cleared when there is a hidden test region?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN HIDDEN TESTS
            assert True
            ### END HIDDEN TESTS
            """
        ).strip()
        cell.metadata['nbgrader'] = dict(grade=True)

        resources = dict()
        cell = preprocessor.preprocess_cell(cell, resources, 1)[0]
        assert cell.source == "assert True"
        assert cell.metadata.nbgrader['grade']

    def test_preprocess_text_grade_cell_region_indented(self, preprocessor):
        """Is a text grade cell correctly cleared and indented when there is a hidden test region?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            assert True
                ### BEGIN HIDDEN TESTS
                assert True
                ### END HIDDEN TESTS
            """
        ).strip()
        cell.metadata['nbgrader'] = dict(grade=True)
        resources = dict()

        cell = preprocessor.preprocess_cell(cell, resources, 1)[0]
        assert cell.source == "assert True"
        assert cell.metadata.nbgrader['grade']

    def test_preprocess_text_cell_metadata(self, preprocessor):
        """Is an error thrown when a hidden test region exists in a non-grade text cell?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN HIDDEN TESTS
            assert True
            ### END HIDDEN TESTS
            """
        ).strip()

        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

        # now disable enforcing metadata
        preprocessor.enforce_metadata = False
        cell, _ = preprocessor.preprocess_cell(cell, resources, 1)
        assert cell.source == "assert True"
        assert 'nbgrader' not in cell.metadata

    def test_dont_remove_hidden_test_region(self, preprocessor):
        """Is false returned when there is no hidden test region?"""
        cell = create_text_cell()
        removed_test = preprocessor._remove_hidden_test_region(cell)
        assert not removed_test

    def test_preprocess_code_cell_no_region(self, preprocessor):
        """Is a code cell not cleared when there is no hidden test region?"""
        cell = create_code_cell()
        cell.source = """assert True"""
        cell.metadata['nbgrader'] = dict()

        resources = dict()
        cell = preprocessor.preprocess_cell(cell, resources, 1)[0]
        assert cell.source == """assert True"""
        assert not cell.metadata.nbgrader.get('grade', False)

    def test_preprocess_text_cell_no_region(self, preprocessor):
        """Is a text grade cell not cleared when there is no hidden test region?"""
        cell = create_text_cell()
        cell.source = """assert True"""
        cell.metadata['nbgrader'] = dict()

        resources = dict()
        cell = preprocessor.preprocess_cell(cell, resources, 1)[0]
        assert cell.source == "assert True"
        assert not cell.metadata.nbgrader.get('grade', False)

    def test_preprocess_notebook(self, preprocessor):
        """Is the test notebook processed without error?"""
        nb = self._read_nb(os.path.join("files", "test.ipynb"))
        preprocessor.preprocess(nb, {})

    def test_remove_celltoolbar(self, preprocessor):
        """Is the celltoolbar removed?"""
        nb = self._read_nb(os.path.join("files", "test.ipynb"))
        nb.metadata['celltoolbar'] = 'Create Assignment'
        nb = preprocessor.preprocess(nb, {})[0]
        assert 'celltoolbar' not in nb.metadata
