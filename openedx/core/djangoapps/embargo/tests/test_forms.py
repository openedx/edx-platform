# -*- coding: utf-8 -*-
"""
Unit tests for embargo app admin forms.
"""

from django.test import TestCase

from opaque_keys.edx.locator import CourseLocator

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from ..models import IPFilter
from ..forms import RestrictedCourseForm, IPFilterForm

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class RestrictedCourseFormTest(ModuleStoreTestCase):
    """Test the course form properly validates course IDs"""

    def test_save_valid_data(self):
        course = CourseFactory.create()
        data = {
            'course_key': unicode(course.id),
            'enroll_msg_key': 'default',
            'access_msg_key': 'default'
        }
        form = RestrictedCourseForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_course_key(self):
        # Invalid format for the course key
        form = RestrictedCourseForm(data={'course_key': 'not/valid'})
        self._assert_course_field_error(form)

    def test_course_not_found(self):
        course_key = CourseLocator(org='test', course='test', run='test')
        form = RestrictedCourseForm(data={'course_key': course_key})
        self._assert_course_field_error(form)

    def _assert_course_field_error(self, form):
        """
        Validation shouldn't work.
        """
        self.assertFalse(form.is_valid())

        msg = 'COURSE NOT FOUND'
        self.assertIn(msg, form._errors['course_key'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(
            ValueError, "The RestrictedCourse could not be created because the data didn't validate."
        ):
            form.save()


class IPFilterFormTest(TestCase):
    """Test form for adding [black|white]list IP addresses"""

    def tearDown(self):
        super(IPFilterFormTest, self).tearDown()
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()

    def test_add_valid_ips(self):
        # test adding valid ip addresses
        # should be able to do both ipv4 and ipv6
        # spacing should not matter
        form_data = {
            'whitelist': '127.0.0.1, 2003:dead:beef:4dad:23:46:bb:101, 1.1.0.1/32, 1.0.0.0/24',
            'blacklist': '  18.244.1.5  ,  2002:c0a8:101::42, 18.36.22.1, 1.0.0.0/16'
        }
        form = IPFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        whitelist = IPFilter.current().whitelist_ips
        blacklist = IPFilter.current().blacklist_ips
        for addr in '127.0.0.1, 2003:dead:beef:4dad:23:46:bb:101'.split(','):
            self.assertIn(addr.strip(), whitelist)
        for addr in '18.244.1.5, 2002:c0a8:101::42, 18.36.22.1'.split(','):
            self.assertIn(addr.strip(), blacklist)

        # Network tests
        # ips not in whitelist network
        for addr in ['1.1.0.2', '1.0.1.0']:
            self.assertNotIn(addr.strip(), whitelist)
        # ips in whitelist network
        for addr in ['1.1.0.1', '1.0.0.100']:
            self.assertIn(addr.strip(), whitelist)
        # ips not in blacklist network
        for addr in ['2.0.0.0', '1.1.0.0']:
            self.assertNotIn(addr.strip(), blacklist)
        # ips in blacklist network
        for addr in ['1.0.100.0', '1.0.0.10']:
            self.assertIn(addr.strip(), blacklist)

        # Test clearing by adding an empty list is OK too
        form_data = {
            'whitelist': '',
            'blacklist': ''
        }
        form = IPFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(IPFilter.current().whitelist), 0)
        self.assertEqual(len(IPFilter.current().blacklist), 0)

    def test_add_invalid_ips(self):
        # test adding invalid ip addresses
        form_data = {
            'whitelist': '.0.0.1, :dead:beef:::, 1.0.0.0/55',
            'blacklist': '  18.244.*  ,  999999:c0a8:101::42, 1.0.0.0/'
        }
        form = IPFilterForm(data=form_data)
        self.assertFalse(form.is_valid())

        wmsg = "Invalid IP Address(es): [u'.0.0.1', u':dead:beef:::', u'1.0.0.0/55']" \
               " Please fix the error(s) and try again."
        self.assertEquals(wmsg, form._errors['whitelist'][0])  # pylint: disable=protected-access
        bmsg = "Invalid IP Address(es): [u'18.244.*', u'999999:c0a8:101::42', u'1.0.0.0/']" \
               " Please fix the error(s) and try again."
        self.assertEquals(bmsg, form._errors['blacklist'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The IPFilter could not be created because the data didn't validate."):
            form.save()
