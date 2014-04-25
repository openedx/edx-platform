# -*- coding: utf-8 -*-
"""
Unit tests for embargo app admin forms.
"""

from django.test import TestCase
from django.test.utils import override_settings

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from embargo.forms import EmbargoedCourseForm, EmbargoedStateForm, IPFilterForm
from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class EmbargoCourseFormTest(ModuleStoreTestCase):
    """Test the course form properly validates course IDs"""

    def setUp(self):
        self.course = CourseFactory.create()
        self.true_form_data = {'course_id': self.course.id.to_deprecated_string(), 'embargoed': True}
        self.false_form_data = {'course_id': self.course.id.to_deprecated_string(), 'embargoed': False}

    def test_embargo_course(self):
        self.assertFalse(EmbargoedCourse.is_embargoed(self.course.id))
        # Test adding embargo to this course
        form = EmbargoedCourseForm(data=self.true_form_data)
        # Validation should work
        self.assertTrue(form.is_valid())
        form.save()
        # Check that this course is embargoed
        self.assertTrue(EmbargoedCourse.is_embargoed(self.course.id))

    def test_repeat_course(self):
        # Initially course shouldn't be authorized
        self.assertFalse(EmbargoedCourse.is_embargoed(self.course.id))
        # Test authorizing the course, which should totally work
        form = EmbargoedCourseForm(data=self.true_form_data)
        # Validation should work
        self.assertTrue(form.is_valid())
        form.save()
        # Check that this course is authorized
        self.assertTrue(EmbargoedCourse.is_embargoed(self.course.id))

        # Now make a new course authorization with the same course id that tries to turn email off
        form = EmbargoedCourseForm(data=self.false_form_data)
        # Validation should not work because course_id field is unique
        self.assertFalse(form.is_valid())
        self.assertEquals(
            "Embargoed course with this Course id already exists.",
            form._errors['course_id'][0]  # pylint: disable=protected-access
        )
        with self.assertRaisesRegexp(ValueError, "The EmbargoedCourse could not be created because the data didn't validate."):
            form.save()

        # Course should still be authorized (invalid attempt had no effect)
        self.assertTrue(EmbargoedCourse.is_embargoed(self.course.id))

    def test_form_typo(self):
        # Munge course id
        bad_id = self.course.id.to_deprecated_string() + '_typo'

        form_data = {'course_id': bad_id, 'embargoed': True}
        form = EmbargoedCourseForm(data=form_data)
        # Validation shouldn't work
        self.assertFalse(form.is_valid())

        msg = 'COURSE NOT FOUND'
        msg += u' --- Entered course id was: "{0}". '.format(bad_id)
        msg += 'Please recheck that you have supplied a valid course id.'
        self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The EmbargoedCourse could not be created because the data didn't validate."):
            form.save()

    def test_invalid_location(self):
        # Munge course id
        bad_id = self.course.id.to_deprecated_string().split('/')[-1]

        form_data = {'course_id': bad_id, 'embargoed': True}
        form = EmbargoedCourseForm(data=form_data)
        # Validation shouldn't work
        self.assertFalse(form.is_valid())

        msg = 'COURSE NOT FOUND'
        msg += u' --- Entered course id was: "{0}". '.format(bad_id)
        msg += 'Please recheck that you have supplied a valid course id.'
        self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The EmbargoedCourse could not be created because the data didn't validate."):
            form.save()


class EmbargoedStateFormTest(TestCase):
    """Test form for adding new states"""

    def setUp(self):
        # Explicitly clear the cache, since ConfigurationModel relies on the cache
        cache.clear()

    def tearDown(self):
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()

    def test_add_valid_states(self):
        # test adding valid two letter states
        # case and spacing should not matter
        form_data = {'embargoed_countries': 'cu, Sy ,      US'}
        form = EmbargoedStateForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        current_embargoes = EmbargoedState.current().embargoed_countries_list
        for country in ["CU", "SY", "US"]:
            self.assertIn(country, current_embargoes)
        # Test clearing by adding an empty list is OK too
        form_data = {'embargoed_countries': ''}
        form = EmbargoedStateForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(len(EmbargoedState.current().embargoed_countries_list) == 0)

    def test_add_invalid_states(self):
        # test adding invalid codes
        # xx is not valid
        # usa is not valid
        form_data = {'embargoed_countries': 'usa, xx'}
        form = EmbargoedStateForm(data=form_data)
        self.assertFalse(form.is_valid())

        msg = 'COULD NOT PARSE COUNTRY CODE(S) FOR: {0}'.format([u'USA', u'XX'])
        msg += ' Please check the list of country codes and verify your entries.'
        self.assertEquals(msg, form._errors['embargoed_countries'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The EmbargoedState could not be created because the data didn't validate."):
            form.save()

        self.assertFalse('USA' in EmbargoedState.current().embargoed_countries_list)
        self.assertFalse('XX' in EmbargoedState.current().embargoed_countries_list)


class IPFilterFormTest(TestCase):
    """Test form for adding [black|white]list IP addresses"""

    def tearDown(self):
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()

    def test_add_valid_ips(self):
        # test adding valid ip addresses
        # should be able to do both ipv4 and ipv6
        # spacing should not matter
        form_data = {
            'whitelist': '127.0.0.1, 2003:dead:beef:4dad:23:46:bb:101',
            'blacklist': '  18.244.1.5  ,  2002:c0a8:101::42, 18.36.22.1'
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

        # Test clearing by adding an empty list is OK too
        form_data = {
            'whitelist': '',
            'blacklist': ''
        }
        form = IPFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(len(IPFilter.current().whitelist) == 0)
        self.assertTrue(len(IPFilter.current().blacklist) == 0)

    def test_add_invalid_ips(self):
        # test adding invalid ip addresses
        form_data = {
            'whitelist': '.0.0.1, :dead:beef:::',
            'blacklist': '  18.244.*  ,  999999:c0a8:101::42'
        }
        form = IPFilterForm(data=form_data)
        self.assertFalse(form.is_valid())

        wmsg = "Invalid IP Address(es): [u'.0.0.1', u':dead:beef:::'] Please fix the error(s) and try again."
        self.assertEquals(wmsg, form._errors['whitelist'][0])  # pylint: disable=protected-access
        bmsg = "Invalid IP Address(es): [u'18.244.*', u'999999:c0a8:101::42'] Please fix the error(s) and try again."
        self.assertEquals(bmsg, form._errors['blacklist'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The IPFilter could not be created because the data didn't validate."):
            form.save()
