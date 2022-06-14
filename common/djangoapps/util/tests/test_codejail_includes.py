"""
Tests for codejail-includes package.
"""

import unittest

import eia
import loncapa
from verifiers import draganddrop


class TestCodeJailIncludes(unittest.TestCase):
    """ tests for  codejail includes"""

    def test_loncapa(self):
        random_integer = loncapa.lc_random(2, 60, 5)
        assert random_integer <= 60
        assert random_integer >= 2

    def test_nested_list_and_list1(self):
        assert draganddrop.PositionsCompare([[1, 2], 40]) == draganddrop.PositionsCompare([1, 3])

    def test_Eia(self):
        # Test cases. All of these should return True
        assert eia.iseia(100)  # 100 ohm resistor is EIA
        assert not eia.iseia(101)  # 101 is not
