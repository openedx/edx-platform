import pytest
import os

from ...preprocessors import IncludeHeaderFooter
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessor():
    return IncludeHeaderFooter()


class TestIncludeHeaderFooter(BaseTestPreprocessor):

    def test_concatenate_nothing(self, preprocessor):
        """Are the cells the same if there is no header or footer?"""
        orig_nb = self._read_nb(os.path.join("files", "test.ipynb"))
        nb = preprocessor.preprocess(orig_nb, {})[0]
        assert nb == orig_nb

    def test_concatenate_header(self, preprocessor):
        """Is the header prepended correctly?"""
        preprocessor.header = os.path.join(os.path.dirname(__file__), "files", "header.ipynb")
        cells = self._read_nb(os.path.join("files", "header.ipynb")).cells[:]
        orig_nb = self._read_nb(os.path.join("files", "test.ipynb"))
        orig_cells = orig_nb.cells[:]
        nb = preprocessor.preprocess(orig_nb, {})[0]
        assert nb.cells == (cells + orig_cells)

    def test_concatenate_footer(self, preprocessor):
        """Is the footer appended correctly?"""
        preprocessor.footer = os.path.join(os.path.dirname(__file__), "files", "header.ipynb")
        cells = self._read_nb(os.path.join("files", "header.ipynb")).cells[:]
        orig_nb = self._read_nb(os.path.join("files", "test.ipynb"))
        orig_cells = orig_nb.cells[:]
        nb = preprocessor.preprocess(orig_nb, {})[0]
        assert nb.cells == (orig_cells + cells)

    def test_concatenate_header_and_footer(self, preprocessor):
        """Are the header and footer appended correctly?"""
        preprocessor.header = os.path.join(os.path.dirname(__file__), "files", "header.ipynb")
        preprocessor.footer = os.path.join(os.path.dirname(__file__), "files", "header.ipynb")
        header_cells = self._read_nb(os.path.join("files", "header.ipynb")).cells[:]
        footer_cells = self._read_nb(os.path.join("files", "header.ipynb")).cells[:]
        orig_nb = self._read_nb(os.path.join("files", "test.ipynb"))
        orig_cells = orig_nb.cells[:]
        nb = preprocessor.preprocess(orig_nb, {})[0]
        assert nb.cells == (header_cells + orig_cells + footer_cells)
