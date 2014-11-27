"""
Unit tests for the classes in library_content_module.py
"""
from bson import ObjectId
import ddt
from mock import Mock, patch
import random
import unittest
from collections import namedtuple
from opaque_keys.edx.locator import LibraryLocator

from xmodule.library_content_module import (
    LibraryVersionReference, LibraryList, LibraryContentModule,
    LibraryContentFields, LibraryContentDescriptor
)


@ddt.ddt
class TestLibraryVersionReference(unittest.TestCase):
    """ Tests for LibraryVersionReference """
    # pylint: disable=no-member
    # ^ because pylint currently raises no-member for any use of namedtuple
    def test_init_from_string_without_version(self):
        locator = LibraryLocator("TestX", "LIB")

        lvr = LibraryVersionReference(unicode(locator))

        self.assertEquals(lvr.library_id, locator)
        self.assertEquals(lvr.version, locator.version)
        self.assertIsNone(lvr.version)

    def test_init_from_course_locator_without_version(self):
        locator = LibraryLocator("TestX", "LIB")

        lvr = LibraryVersionReference(locator)

        self.assertEquals(lvr.library_id, locator)
        self.assertEquals(lvr.version, locator.version)
        self.assertIsNone(lvr.version)

    def test_init_from_course_locator_and_version(self):
        version = ObjectId()
        locator = LibraryLocator("TestX", "LIB")

        lvr = LibraryVersionReference(locator, version)

        self.assertEquals(lvr.library_id, locator)
        self.assertEquals(lvr.version, version)

    def test_init_from_lib_locator_and_matching_version(self):
        version = ObjectId()
        locator = LibraryLocator("TestX", "LIB", version_guid=version)
        expected_locator = locator.for_version(None)

        lvr = LibraryVersionReference(locator, version)

        self.assertEquals(lvr.library_id, expected_locator)
        self.assertEquals(lvr.version, version)

    def test_init_throws_if_version_mismatch(self):
        version = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
        locator = LibraryLocator("TestX", "LIB", version_guid=ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb"))

        with self.assertRaises(AssertionError):
            LibraryVersionReference(locator, version)

    @ddt.data(
        ["library-v1:TestX+TEST", "abcdefabcdefabcdefabcdef"],
    )
    @ddt.unpack
    def test_from_json(self, expected_locator, expected_version):
        lvr = LibraryVersionReference.from_json([expected_locator, expected_version])
        self.assertEquals(unicode(lvr.library_id), expected_locator)
        self.assertEquals(lvr.version, ObjectId(expected_version))

    @ddt.data(
        ["library-v1:TestX+TEST", "abcdefabcdefabcdefabcdef"],
        ["library-v1:TestX+TEST", None],
    )
    def test_json_roundtrip(self, expected):
        result = LibraryVersionReference.from_json(expected).to_json()
        self.assertEquals(expected, result)


class TestLibraryList(unittest.TestCase):
    """ Tests for LibraryList """
    def test_json_roundtrip(self):
        json_data = [
            ["library-v1:TestX+TEST", "abcdefabcdefabcdefabcdef"],
            ["library-v1:TestX+OTHER", "efabcdefabcdefabcdefabcd"],
        ]

        lib_list = LibraryList()

        self.assertEquals(lib_list.to_json(lib_list.from_json(json_data)), json_data)

    def test_from_json(self):
        json_data = [
            ["library-v1:TestX+TEST", "abcdefabcdefabcdefabcdef"],
            ["library-v1:TestX+OTHER", "efabcdefabcdefabcdefabcd"],
        ]
        expected = [LibraryVersionReference.from_json(a) for a in json_data]

        lib_list = LibraryList()

        self.assertEquals(lib_list.from_json(json_data), expected)


LCM = LibraryContentModule


@patch.object(LCM, "source_libraries", LCM.source_libraries.default)
@patch.object(LCM, "mode", LCM.mode.default)
@patch.object(LCM, "max_count", LCM.max_count.default)
@patch.object(LCM, "filters", LCM.filters.default)
@patch.object(LCM, "selected", LCM.selected.default)
@patch.object(LCM, "has_score", LCM.has_score.default)  # pylint: disable=maybe-no-member
@patch.object(LCM, "children", [])
class TestLibraryContentModule(unittest.TestCase):
    """ Tests for LibraryContentModule """
    def setUp(self):
        # Mocking out base classes of LibraryContentModule
        self._orig_bases = LibraryContentModule.__bases__
        LibraryContentModule.__bases__ = (LibraryContentFields,)
        # just making sure that tests are reproducible
        self._orig_random_state = random.getstate()
        random.seed(42)

        # more verbose than assertTrue(a.issubset(b))
        self.assert_is_subset = self.assertLessEqual

    def tearDown(self):
        random.setstate(self._orig_random_state)
        LibraryContentModule.__bases__ = self._orig_bases

    def _set_up_lcm(self, num_child, max_count, selected=None, mode="random"):
        """ Create an instance of LibraryContentModule with mock children """
        assert mode in ["random", "first"]
        if selected is None:
            selected = []

        lcm = LibraryContentModule()

        MockChildBlock = namedtuple('XBlock', "block_id")  # pylint: disable=invalid-name
        lcm.children = [MockChildBlock(i) for i in range(num_child)]

        lcm.max_count = max_count
        lcm.selected = selected
        lcm.mode = mode

        all_block_ids = set(c.block_id for c in lcm.children)

        return lcm, all_block_ids

    def _assert_consistent_selection(self, selected, lcm, all_block_ids):
        """ Helper for following tests of the 'selected' property """
        max_elements = min(lcm.max_count, len(lcm.children))
        self.assertEqual(len(selected), max_elements)
        self.assertEqual(selected, set(lcm.selected))
        self.assert_is_subset(selected, all_block_ids)

    def test_selected_children_filled_from_children(self):
        lcm, all_block_ids = self._set_up_lcm(num_child=10, max_count=5)

        selection = lcm.selected_children()

        self._assert_consistent_selection(selection, lcm, all_block_ids)

    def test_selected_children_returns_all_from_small_pool(self):
        lcm, all_block_ids = self._set_up_lcm(num_child=4, max_count=6)

        selection = lcm.selected_children()

        self._assert_consistent_selection(selection, lcm, all_block_ids)
        self.assertEqual(selection, all_block_ids)

    def test_selected_children_fixes_selected_with_invalid_ids(self):
        lcm, all_block_ids = self._set_up_lcm(8, 5, selected=[-3, 1, 5, 9, 15])
        old_but_valid_ids = set(lcm.selected) & all_block_ids

        selection = lcm.selected_children()

        self._assert_consistent_selection(selection, lcm, all_block_ids)
        self.assert_is_subset(old_but_valid_ids, selection)

    def test_selected_children_fixes_selected_with_too_many_ids(self):
        lcm, all_block_ids = self._set_up_lcm(12, 4, selected=list(range(8)))
        orig_selected = set(lcm.selected)

        selection = lcm.selected_children()

        self._assert_consistent_selection(selection, lcm, all_block_ids)
        self.assert_is_subset(selection, set(orig_selected))

    def test_calling_selected_children_multiple_times_returns_same_result(self):
        lcm, all_block_ids = self._set_up_lcm(13, 7)

        selections = [lcm.selected_children() for _ in range(10)]

        for selection in selections:
            self._assert_consistent_selection(selection, lcm, all_block_ids)
        for sel1, sel2 in zip(selections, selections[1:]):
            self.assertEquals(sel1, sel2)


class TestLibraryContentDescriptor(unittest.TestCase):
    """ Tests for LibraryContentDescriptor """
    def test_has_dynamic_children_returns_true(self):
        lcd = LibraryContentDescriptor(Mock(), Mock(), Mock())
        self.assertTrue(lcd.has_dynamic_children())
