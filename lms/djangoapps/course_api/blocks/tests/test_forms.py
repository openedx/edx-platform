"""
Tests for Course Blocks forms
"""
import ddt
from django.http import Http404, QueryDict
from unittest import TestCase
from urllib import urlencode
from rest_framework.exceptions import PermissionDenied

from student.tests.factories import UserFactory
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.util.test_forms import FormTestMixin
from ..forms import BlockListGetForm


@ddt.ddt
class TestBlockListGetForm(FormTestMixin, TestCase):
    """
    Tests for BlockListGetForm
    """
    FORM_CLASS = BlockListGetForm

    def setUp(self):
        self.student = UserFactory.create()
        self.student2 = UserFactory.create()
        self.staff = UserFactory.create(is_staff=True)
        self.initial = {'requesting_user': self.student}

        usage_key_string = 'block-v1:some_org+split_course+some_run+type@some_block_type+block@some_block_id'
        self.form_data = QueryDict(
            urlencode({
                'user': self.student.username,
                'usage_key': usage_key_string,
            }),
            mutable=True,
        )
        self.cleaned_data = {
            'block_counts': [],
            'depth': 0,
            'requested_fields': {'display_name', 'type'},
            'student_view_data': [],
            'usage_key': UsageKey.from_string(usage_key_string),
            'user': self.student,
        }

    def assert_raises_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            self.get_form(expected_valid=False)

    def assert_raises_not_found(self):
        with self.assertRaises(Http404):
            self.get_form(expected_valid=False)

    def assert_equals_cleaned_data(self):
        form = self.get_form(expected_valid=True)
        self.assertEqual(form.cleaned_data, self.cleaned_data)

    def test_basic(self):
        self.assert_equals_cleaned_data()

    #-- usage key

    def test_missing_usage_key(self):
        self.form_data.pop('usage_key')
        self.assert_error('usage_key', "This field is required.")

    def test_invalid_usage_key(self):
        self.form_data['usage_key'] = 'invalid_usage_key'
        self.assert_error('usage_key', "'invalid_usage_key' is not a valid usage key.")

    #-- user

    def test_missing_user(self):
        self.form_data.pop('user')
        self.assert_raises_permission_denied()

    def test_nonexistent_user_by_student(self):
        self.form_data['user'] = 'non_existent_user'
        self.assert_raises_permission_denied()

    def test_nonexistent_user_by_staff(self):
        self.initial = {'requesting_user': self.staff}
        self.form_data['user'] = 'non_existent_user'
        self.assert_raises_not_found()

    def test_other_user_by_student(self):
        self.form_data['user'] = self.student2.username
        self.assert_raises_permission_denied()

    def test_other_user_by_staff(self):
        self.initial = {'requesting_user': self.staff}
        self.get_form(expected_valid=True)

    #-- depth

    def test_depth_integer(self):
        self.form_data['depth'] = 3
        self.cleaned_data['depth'] = 3
        self.assert_equals_cleaned_data()

    def test_depth_all(self):
        self.form_data['depth'] = 'all'
        self.cleaned_data['depth'] = None
        self.assert_equals_cleaned_data()

    def test_depth_invalid(self):
        self.form_data['depth'] = 'not_an_integer'
        self.assert_error('depth', "'not_an_integer' is not a valid depth value.")

    #-- requested fields

    def test_requested_fields(self):
        self.form_data.setlist('requested_fields', ['graded', 'some_other_field'])
        self.cleaned_data['requested_fields'] |= {'graded', 'some_other_field'}
        self.assert_equals_cleaned_data()

    @ddt.data('block_counts', 'student_view_data')
    def test_higher_order_field(self, field_name):
        field_value = ['block_type1', 'block_type2']
        self.form_data.setlist(field_name, field_value)
        self.cleaned_data[field_name] = field_value
        self.cleaned_data['requested_fields'].add(field_name)
        self.assert_equals_cleaned_data()

    def test_combined_fields(self):
        # add requested fields
        self.form_data.setlist('requested_fields', ['field1', 'field2'])

        # add higher order fields
        block_types_list = ['block_type1', 'block_type2']
        for field_name in ['block_counts', 'student_view_data']:
            self.form_data.setlist(field_name, block_types_list)
            self.cleaned_data[field_name] = block_types_list

        # verify the requested_fields in cleaned_data includes all fields
        self.cleaned_data['requested_fields'] |= {'field1', 'field2', 'student_view_data', 'block_counts'}
        self.assert_equals_cleaned_data()
