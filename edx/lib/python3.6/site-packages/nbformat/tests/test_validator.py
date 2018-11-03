"""Test nbformat.validator"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from .base import TestsBase
from jsonschema import ValidationError
from nbformat import read
from ..validator import isvalid, validate


class TestValidator(TestsBase):

    def test_nb2(self):
        """Test that a v2 notebook converted to current passes validation"""
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb3(self):
        """Test that a v3 notebook passes validation"""
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb4(self):
        """Test that a v4 notebook passes validation"""
        with self.fopen(u'test4.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb4_document_info(self):
        """Test that a notebook with document_info passes validation"""
        with self.fopen(u'test4docinfo.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb4custom(self):
        """Test that a notebook with a custom JSON mimetype passes validation"""
        with self.fopen(u'test4custom.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_nb4jupyter_metadata(self):
        """Test that a notebook with a jupyter metadata passes validation"""
        with self.fopen(u'test4jupyter_metadata.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        validate(nb)
        self.assertEqual(isvalid(nb), True)

    def test_invalid(self):
        """Test than an invalid notebook does not pass validation"""
        # this notebook has a few different errors:
        # - one cell is missing its source
        # - invalid cell type
        # - invalid output_type
        with self.fopen(u'invalid.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        with self.assertRaises(ValidationError):
            validate(nb)
        self.assertEqual(isvalid(nb), False)

    def test_validate_empty(self):
        """Test that an empty dict can be validated without error"""
        validate({})

    def test_future(self):
        """Test than a notebook from the future with extra keys passes validation"""
        with self.fopen(u'test4plus.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        with self.assertRaises(ValidationError):
            validate(nb, version=4)

        self.assertEqual(isvalid(nb, version=4), False)
        self.assertEqual(isvalid(nb), True)

    def test_validation_error(self):
        with self.fopen(u'invalid.ipynb', u'r') as f:
            nb = read(f, as_version=4)
        with self.assertRaises(ValidationError) as e:
            validate(nb)
        s = str(e.exception)
        self.assertRegexpMatches(s, "validating.*required.* in markdown_cell")
        self.assertRegexpMatches(s, "source.* is a required property")
        self.assertRegexpMatches(s, r"On instance\[u?['\"].*cells['\"]\]\[0\]")
        self.assertLess(len(s.splitlines()), 10)
