"""
Tests for Discussion API forms
"""
from unittest import TestCase

from opaque_keys.edx.locator import CourseLocator

from discussion_api.forms import CommentListGetForm, ThreadListGetForm


class FormTestMixin(object):
    """A mixin for testing forms"""
    def get_form(self, expected_valid):
        """
        Return a form bound to self.form_data, asserting its validity (or lack
        thereof) according to expected_valid
        """
        form = self.FORM_CLASS(self.form_data)
        self.assertEqual(form.is_valid(), expected_valid)
        return form

    def assert_error(self, expected_field, expected_message):
        """
        Create a form bound to self.form_data, assert its invalidity, and assert
        that its error dictionary contains one entry with the expected field and
        message
        """
        form = self.get_form(expected_valid=False)
        self.assertEqual(form.errors, {expected_field: [expected_message]})

    def assert_field_value(self, field, expected_value):
        """
        Create a form bound to self.form_data, assert its validity, and assert
        that the given field in the cleaned data has the expected value
        """
        form = self.get_form(expected_valid=True)
        self.assertEqual(form.cleaned_data[field], expected_value)


class PaginationTestMixin(object):
    """A mixin for testing forms with pagination fields"""
    def test_missing_page(self):
        self.form_data.pop("page")
        self.assert_field_value("page", 1)

    def test_invalid_page(self):
        self.form_data["page"] = "0"
        self.assert_error("page", "Ensure this value is greater than or equal to 1.")

    def test_missing_page_size(self):
        self.form_data.pop("page_size")
        self.assert_field_value("page_size", 10)

    def test_zero_page_size(self):
        self.form_data["page_size"] = "0"
        self.assert_error("page_size", "Ensure this value is greater than or equal to 1.")

    def test_excessive_page_size(self):
        self.form_data["page_size"] = "101"
        self.assert_field_value("page_size", 100)


class ThreadListGetFormTest(FormTestMixin, PaginationTestMixin, TestCase):
    """Tests for ThreadListGetForm"""
    FORM_CLASS = ThreadListGetForm

    def setUp(self):
        super(ThreadListGetFormTest, self).setUp()
        self.form_data = {
            "course_id": "Foo/Bar/Baz",
            "page": "2",
            "page_size": "13",
        }

    def test_basic(self):
        form = self.get_form(expected_valid=True)
        self.assertEqual(
            form.cleaned_data,
            {
                "course_id": CourseLocator.from_string("Foo/Bar/Baz"),
                "page": 2,
                "page_size": 13,
            }
        )

    def test_missing_course_id(self):
        self.form_data.pop("course_id")
        self.assert_error("course_id", "This field is required.")

    def test_invalid_course_id(self):
        self.form_data["course_id"] = "invalid course id"
        self.assert_error("course_id", "'invalid course id' is not a valid course id")


class CommentListGetFormTest(FormTestMixin, PaginationTestMixin, TestCase):
    """Tests for CommentListGetForm"""
    FORM_CLASS = CommentListGetForm

    def setUp(self):
        super(CommentListGetFormTest, self).setUp()
        self.form_data = {
            "thread_id": "deadbeef",
            "endorsed": "False",
            "page": "2",
            "page_size": "13",
        }

    def test_basic(self):
        form = self.get_form(expected_valid=True)
        self.assertEqual(
            form.cleaned_data,
            {
                "thread_id": "deadbeef",
                "endorsed": False,
                "page": 2,
                "page_size": 13,
            }
        )

    def test_missing_thread_id(self):
        self.form_data.pop("thread_id")
        self.assert_error("thread_id", "This field is required.")

    def test_missing_endorsed(self):
        self.form_data.pop("endorsed")
        self.assert_field_value("endorsed", None)
