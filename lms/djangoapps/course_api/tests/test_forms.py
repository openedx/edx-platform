"""
Tests for Course API forms.
"""

import ddt
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from itertools import product
from urllib import urlencode

from openedx.core.djangoapps.util.test_forms import FormTestMixin
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..forms import CourseDetailGetForm, CourseListGetForm


class UsernameTestMixin(object):
    """
    Tests the username Form field.
    """
    def test_no_user_param_anonymous_access(self):
        self.set_up_data(AnonymousUser())
        self.form_data.pop('username')
        self.assert_valid(self.cleaned_data)

    def test_no_user_param(self):
        self.form_data.pop('username')
        self.assert_error('username', "A username is required for non-anonymous access.")


@ddt.ddt
class TestCourseListGetForm(FormTestMixin, UsernameTestMixin, SharedModuleStoreTestCase):
    """
    Tests for CourseListGetForm
    """
    FORM_CLASS = CourseListGetForm

    @classmethod
    def setUpClass(cls):
        super(TestCourseListGetForm, cls).setUpClass()

        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestCourseListGetForm, self).setUp()

        self.student = UserFactory.create()
        self.set_up_data(self.student)

    def set_up_data(self, user):
        """
        Sets up the initial form data and the expected clean data.
        """
        self.initial = {'requesting_user': user}
        self.form_data = QueryDict(
            urlencode({
                'username': user.username,
            }),
            mutable=True,
        )
        self.cleaned_data = {
            'username': user.username,
            'org': '',
            'mobile': None,
            'filter_': None,
        }

    def test_basic(self):
        self.assert_valid(self.cleaned_data)

    def test_org(self):
        org_value = 'test org name'
        self.form_data['org'] = org_value
        self.cleaned_data['org'] = org_value
        self.assert_valid(self.cleaned_data)

    @ddt.data(
        *product(
            [('mobile', 'mobile_available')],
            [(True, True), (False, False), ('1', True), ('0', False), (None, None)],
        )
    )
    @ddt.unpack
    def test_filter(self, param_field_name, param_field_value):
        param_name, field_name = param_field_name
        param_value, field_value = param_field_value

        self.form_data[param_name] = param_value
        self.cleaned_data[param_name] = field_value
        if field_value is not None:
            self.cleaned_data['filter_'] = {field_name: field_value}

        self.assert_valid(self.cleaned_data)


class TestCourseDetailGetForm(FormTestMixin, UsernameTestMixin, SharedModuleStoreTestCase):
    """
    Tests for CourseDetailGetForm
    """
    FORM_CLASS = CourseDetailGetForm

    @classmethod
    def setUpClass(cls):
        super(TestCourseDetailGetForm, cls).setUpClass()

        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestCourseDetailGetForm, self).setUp()

        self.student = UserFactory.create()
        self.set_up_data(self.student)

    def set_up_data(self, user):
        """
        Sets up the initial form data and the expected clean data.
        """
        self.initial = {'requesting_user': user}
        self.form_data = QueryDict(
            urlencode({
                'username': user.username,
                'course_key': unicode(self.course.id),
            }),
            mutable=True,
        )
        self.cleaned_data = {
            'username': user.username,
            'course_key': self.course.id,
        }

    def test_basic(self):
        self.assert_valid(self.cleaned_data)

    #-- course key --#

    def test_no_course_key_param(self):
        self.form_data.pop('course_key')
        self.assert_error('course_key', "This field is required.")

    def test_invalid_course_key(self):
        self.form_data['course_key'] = 'invalid_course_key'
        self.assert_error('course_key', "'invalid_course_key' is not a valid course key.")
