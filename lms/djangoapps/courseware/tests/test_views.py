# coding=UTF-8
"""
Tests courseware views.py
"""

from urllib import urlencode, quote
import ddt
import json
import itertools
import unittest
from datetime import datetime, timedelta
from HTMLParser import HTMLParser
from nose.plugins.attrib import attr
from freezegun import freeze_time

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client
from django.test.utils import override_settings
from mock import MagicMock, patch, create_autospec, PropertyMock
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey
from pytz import UTC
from xblock.core import XBlock
from xblock.fields import String, Scope
from xblock.fragment import Fragment

import courseware.views.views as views
import shoppingcart
from certificates import api as certs_api
from certificates.models import CertificateStatuses, CertificateGenerationConfiguration
from certificates.tests.factories import (
    CertificateInvalidationFactory,
    GeneratedCertificateFactory
)
from commerce.models import CommerceConfiguration
from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.model_data import set_score
from courseware.module_render import toc_for_course
from courseware.testutils import RenderXBlockTestMixin
from courseware.tests.factories import StudentModuleFactory, GlobalStaffFactory
from courseware.url_helpers import get_redirect_url
from courseware.user_state_client import DjangoXBlockUserStateClient
from courseware.views.index import render_accordion
from lms.djangoapps.commerce.utils import EcommerceService  # pylint: disable=import-error
from milestones.tests.utils import MilestonesTestCaseMixin
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.lib.gating import api as gating_api
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory, UserFactory, CourseEnrollmentFactory
from util.tests.test_date_utils import fake_ugettext, fake_pgettext
from util.url import reload_django_url_config
from util.views import ensure_valid_course_key
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from openedx.core.djangoapps.credit.api import set_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider


@attr(shard=1)
class TestJumpTo(ModuleStoreTestCase):
    """
    Check the jumpto link for a course.
    """
    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        super(TestJumpTo, self).setUp()
        # Use toy course from XML
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

    def test_jumpto_invalid_location(self):
        location = self.course_key.make_usage_key(None, 'NoSuchPlace')
        # This is fragile, but unfortunately the problem is that within the LMS we
        # can't use the reverse calls from the CMS
        jumpto_url = '{0}/{1}/jump_to/{2}'.format('/courses', unicode(self.course_key), unicode(location))
        response = self.client.get(jumpto_url)
        self.assertEqual(response.status_code, 404)

    @unittest.skip
    def test_jumpto_from_chapter(self):
        location = self.course_key.make_usage_key('chapter', 'Overview')
        jumpto_url = '{0}/{1}/jump_to/{2}'.format('/courses', unicode(self.course_key), unicode(location))
        expected = 'courses/edX/toy/2012_Fall/courseware/Overview/'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

    @unittest.skip
    def test_jumpto_id(self):
        jumpto_url = '{0}/{1}/jump_to_id/{2}'.format('/courses', unicode(self.course_key), 'Overview')
        expected = 'courses/edX/toy/2012_Fall/courseware/Overview/'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

    def test_jumpto_from_section(self):
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        section = ItemFactory.create(category='sequential', parent_location=chapter.location)
        expected = 'courses/{course_id}/courseware/{chapter_id}/{section_id}/?{activate_block_id}'.format(
            course_id=unicode(course.id),
            chapter_id=chapter.url_name,
            section_id=section.url_name,
            activate_block_id=urlencode({'activate_block_id': unicode(section.location)})
        )
        jumpto_url = '{0}/{1}/jump_to/{2}'.format(
            '/courses',
            unicode(course.id),
            unicode(section.location),
        )
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

    def test_jumpto_from_module(self):
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        section = ItemFactory.create(category='sequential', parent_location=chapter.location)
        vertical1 = ItemFactory.create(category='vertical', parent_location=section.location)
        vertical2 = ItemFactory.create(category='vertical', parent_location=section.location)
        module1 = ItemFactory.create(category='html', parent_location=vertical1.location)
        module2 = ItemFactory.create(category='html', parent_location=vertical2.location)

        expected = 'courses/{course_id}/courseware/{chapter_id}/{section_id}/1?{activate_block_id}'.format(
            course_id=unicode(course.id),
            chapter_id=chapter.url_name,
            section_id=section.url_name,
            activate_block_id=urlencode({'activate_block_id': unicode(module1.location)})
        )
        jumpto_url = '{0}/{1}/jump_to/{2}'.format(
            '/courses',
            unicode(course.id),
            unicode(module1.location),
        )
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

        expected = 'courses/{course_id}/courseware/{chapter_id}/{section_id}/2?{activate_block_id}'.format(
            course_id=unicode(course.id),
            chapter_id=chapter.url_name,
            section_id=section.url_name,
            activate_block_id=urlencode({'activate_block_id': unicode(module2.location)})
        )
        jumpto_url = '{0}/{1}/jump_to/{2}'.format(
            '/courses',
            unicode(course.id),
            unicode(module2.location),
        )
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

    def test_jumpto_from_nested_module(self):
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        section = ItemFactory.create(category='sequential', parent_location=chapter.location)
        vertical = ItemFactory.create(category='vertical', parent_location=section.location)
        nested_section = ItemFactory.create(category='sequential', parent_location=vertical.location)
        nested_vertical1 = ItemFactory.create(category='vertical', parent_location=nested_section.location)
        # put a module into nested_vertical1 for completeness
        ItemFactory.create(category='html', parent_location=nested_vertical1.location)
        nested_vertical2 = ItemFactory.create(category='vertical', parent_location=nested_section.location)
        module2 = ItemFactory.create(category='html', parent_location=nested_vertical2.location)

        # internal position of module2 will be 1_2 (2nd item withing 1st item)

        expected = 'courses/{course_id}/courseware/{chapter_id}/{section_id}/1?{activate_block_id}'.format(
            course_id=unicode(course.id),
            chapter_id=chapter.url_name,
            section_id=section.url_name,
            activate_block_id=urlencode({'activate_block_id': unicode(module2.location)})
        )
        jumpto_url = '{0}/{1}/jump_to/{2}'.format(
            '/courses',
            unicode(course.id),
            unicode(module2.location),
        )
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

    def test_jumpto_id_invalid_location(self):
        location = Location('edX', 'toy', 'NoSuchPlace', None, None, None)
        jumpto_url = '{0}/{1}/jump_to_id/{2}'.format('/courses', unicode(self.course_key), unicode(location))
        response = self.client.get(jumpto_url)
        self.assertEqual(response.status_code, 404)


@attr(shard=2)
@ddt.ddt
class ViewsTestCase(ModuleStoreTestCase):
    """
    Tests for views.py methods.
    """

    def setUp(self):
        super(ViewsTestCase, self).setUp()
        self.course = CourseFactory.create(display_name=u'teꜱᴛ course', run="Testing_course")
        self.chapter = ItemFactory.create(
            category='chapter',
            parent_location=self.course.location,
            display_name="Chapter 1",
        )
        self.section = ItemFactory.create(
            category='sequential',
            parent_location=self.chapter.location,
            due=datetime(2013, 9, 18, 11, 30, 00),
            display_name='Sequential 1',
        )
        self.vertical = ItemFactory.create(
            category='vertical',
            parent_location=self.section.location,
            display_name='Vertical 1',
        )
        self.problem = ItemFactory.create(
            category='problem',
            parent_location=self.vertical.location,
            display_name='Problem 1',
        )

        self.section2 = ItemFactory.create(
            category='sequential',
            parent_location=self.chapter.location,
            display_name='Sequential 2',
        )
        self.vertical2 = ItemFactory.create(
            category='vertical',
            parent_location=self.section2.location,
            display_name='Vertical 2',
        )
        self.problem2 = ItemFactory.create(
            category='problem',
            parent_location=self.vertical2.location,
            display_name='Problem 2',
        )

        self.course_key = self.course.id
        self.password = '123456'
        self.user = UserFactory(username='dummy', password=self.password, email='test@mit.edu')
        self.date = datetime(2013, 1, 22, tzinfo=UTC)
        self.enrollment = CourseEnrollment.enroll(self.user, self.course_key)
        self.enrollment.created = self.date
        self.enrollment.save()
        chapter = 'Overview'
        self.chapter_url = '%s/%s/%s' % ('/courses', self.course_key, chapter)

        self.org = u"ꜱᴛᴀʀᴋ ɪɴᴅᴜꜱᴛʀɪᴇꜱ"
        self.org_html = "<p>'+Stark/Industries+'</p>"

        self.assertTrue(self.client.login(username=self.user.username, password=self.password))

        # refresh the course from the modulestore so that it has children
        self.course = modulestore().get_course(self.course.id)

    def test_index_success(self):
        response = self._verify_index_response()
        self.assertIn(unicode(self.problem2.location), response.content.decode("utf-8"))

        # re-access to the main course page redirects to last accessed view.
        url = reverse('courseware', kwargs={'course_id': unicode(self.course_key)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)  # pylint: disable=no-member
        self.assertNotIn(unicode(self.problem.location), response.content.decode("utf-8"))
        self.assertIn(unicode(self.problem2.location), response.content.decode("utf-8"))

    def test_index_nonexistent_chapter(self):
        self._verify_index_response(expected_response_code=404, chapter_name='non-existent')

    def test_index_nonexistent_chapter_masquerade(self):
        with patch('courseware.views.index.setup_masquerade') as patch_masquerade:
            masquerade = MagicMock(role='student')
            patch_masquerade.return_value = (masquerade, self.user)
            self._verify_index_response(expected_response_code=302, chapter_name='non-existent')

    def test_index_nonexistent_section(self):
        self._verify_index_response(expected_response_code=404, section_name='non-existent')

    def test_index_nonexistent_section_masquerade(self):
        with patch('courseware.views.index.setup_masquerade') as patch_masquerade:
            masquerade = MagicMock(role='student')
            patch_masquerade.return_value = (masquerade, self.user)
            self._verify_index_response(expected_response_code=302, section_name='non-existent')

    def _verify_index_response(self, expected_response_code=200, chapter_name=None, section_name=None):
        """
        Verifies the response when the courseware index page is accessed with
        the given chapter and section names.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course_key),
                'chapter': unicode(self.chapter.location.name) if chapter_name is None else chapter_name,
                'section': unicode(self.section2.location.name) if section_name is None else section_name,
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_response_code)
        return response

    def test_index_no_visible_section_in_chapter(self):

        # reload the chapter from the store so its children information is updated
        self.chapter = self.store.get_item(self.chapter.location)

        # disable the visibility of the sections in the chapter
        for section in self.chapter.get_children():
            section.visible_to_staff_only = True
            self.store.update_item(section, ModuleStoreEnum.UserID.test)

        url = reverse(
            'courseware_chapter',
            kwargs={'course_id': unicode(self.course.id), 'chapter': unicode(self.chapter.location.name)},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Problem 1', response.content)
        self.assertNotIn('Problem 2', response.content)

    def _create_global_staff_user(self):
        """
        Create global staff user and log them in
        """
        self.global_staff = GlobalStaffFactory.create()  # pylint: disable=attribute-defined-outside-init
        self.assertTrue(self.client.login(username=self.global_staff.username, password='test'))

    def _create_url_for_enroll_staff(self):
        """
        creates the courseware url and enroll staff url
        """
        # create the _next parameter
        courseware_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course_key),
                'chapter': unicode(self.chapter.location.name),
                'section': unicode(self.section.location.name),
            }
        )
        # create the url for enroll_staff view
        enroll_url = "{enroll_url}?next={courseware_url}".format(
            enroll_url=reverse('enroll_staff', kwargs={'course_id': unicode(self.course.id)}),
            courseware_url=courseware_url
        )
        return courseware_url, enroll_url

    @ddt.data(
        ({'enroll': "Enroll"}, True),
        ({'dont_enroll': "Don't enroll"}, False))
    @ddt.unpack
    def test_enroll_staff_redirection(self, data, enrollment):
        """
        Verify unenrolled staff is redirected to correct url.
        """
        self._create_global_staff_user()
        courseware_url, enroll_url = self._create_url_for_enroll_staff()
        response = self.client.post(enroll_url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        # we were redirected to our current location
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(response.redirect_chain), 1)
        if enrollment:
            self.assertRedirects(response, courseware_url)
        else:
            self.assertRedirects(response, '/courses/{}/about'.format(unicode(self.course_key)))

    def test_enroll_staff_with_invalid_data(self):
        """
        If we try to post with an invalid data pattern, then we'll redirected to
        course about page.
        """
        self._create_global_staff_user()
        __, enroll_url = self._create_url_for_enroll_staff()
        response = self.client.post(enroll_url, data={'test': "test"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/courses/{}/about'.format(unicode(self.course_key)))

    def test_courseware_redirection(self):
        """
        Tests that a global staff member is redirected to the staff enrollment page.

        Un-enrolled Staff user should be redirected to the staff enrollment page accessing courseware,
        user chooses to enroll in the course. User is enrolled and redirected to the requested url.

        Scenario:
            1. Un-enrolled staff tries to access any course vertical (courseware url).
            2. User is redirected to the staff enrollment page.
            3. User chooses to enroll in the course.
            4. User is enrolled in the course and redirected to the requested courseware url.
        """
        self._create_global_staff_user()
        courseware_url, enroll_url = self._create_url_for_enroll_staff()

        # Accessing the courseware url in which not enrolled & redirected to staff enrollment page
        response = self.client.get(courseware_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertRedirects(response, enroll_url)

        # Accessing the enroll staff url and verify the correct url
        response = self.client.get(enroll_url)
        self.assertEqual(response.status_code, 200)
        response_content = response.content
        self.assertIn('Enroll', response_content)
        self.assertIn("dont_enroll", response_content)

        # Post the valid data to enroll the staff in the course
        response = self.client.post(enroll_url, data={'enroll': "Enroll"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertRedirects(response, courseware_url)

        # Verify staff has been enrolled to the given course
        self.assertTrue(CourseEnrollment.is_enrolled(self.global_staff, self.course.id))

    @unittest.skipUnless(settings.FEATURES.get('ENABLE_SHOPPING_CART'), "Shopping Cart not enabled in settings")
    @patch.dict(settings.FEATURES, {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_course_about_in_cart(self):
        in_cart_span = '<span class="add-to-cart">'
        # don't mock this course due to shopping cart existence checking
        course = CourseFactory.create(org="new", number="unenrolled", display_name="course")

        self.client.logout()
        response = self.client.get(reverse('about_course', args=[unicode(course.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(in_cart_span, response.content)

        # authenticated user with nothing in cart
        self.assertTrue(self.client.login(username=self.user.username, password=self.password))
        response = self.client.get(reverse('about_course', args=[unicode(course.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(in_cart_span, response.content)

        # now add the course to the cart
        cart = shoppingcart.models.Order.get_cart_for_user(self.user)
        shoppingcart.models.PaidCourseRegistration.add_to_order(cart, course.id)
        response = self.client.get(reverse('about_course', args=[unicode(course.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(in_cart_span, response.content)

    def assert_enrollment_link_present(self, is_anonymous):
        """
        Prepare ecommerce checkout data and assert if the ecommerce link is contained in the response.

        Arguments:
            is_anonymous(bool): Tell the method to use an anonymous user or the logged in one.
            _id(bool): Tell the method to either expect an id in the href or not.

        """
        checkout_page = '/test_basket/'
        sku = 'TEST123'
        CommerceConfiguration.objects.create(
            checkout_on_ecommerce_service=True,
            single_course_checkout_page=checkout_page
        )
        course = CourseFactory.create()
        CourseModeFactory(mode_slug=CourseMode.PROFESSIONAL, course_id=course.id, sku=sku, min_price=1)

        if is_anonymous:
            self.client.logout()
        else:
            self.assertTrue(self.client.login(username=self.user.username, password=self.password))

        # Construct the link according the following scenarios and verify its presence in the response:
        #      (1) shopping cart is enabled and the user is not logged in
        #      (2) shopping cart is enabled and the user is logged in
        href = '<a href="{uri_stem}?sku={sku}" class="add-to-cart">'.format(uri_stem=checkout_page, sku=sku)

        # Generate the course about page content
        response = self.client.get(reverse('about_course', args=[unicode(course.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(href, response.content)

    @ddt.data(True, False)
    def test_ecommerce_checkout(self, is_anonymous):
        if not is_anonymous:
            self.assert_enrollment_link_present(is_anonymous=is_anonymous)
        else:
            self.assertEqual(EcommerceService().is_enabled(AnonymousUser()), False)

    @ddt.data(True, False)
    @unittest.skipUnless(settings.FEATURES.get('ENABLE_SHOPPING_CART'), 'Shopping Cart not enabled in settings')
    @patch.dict(settings.FEATURES, {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_ecommerce_checkout_shopping_cart_enabled(self, is_anonymous):
        """
        Two scenarios are being validated here -- authenticated/known user and unauthenticated/anonymous user
        For a known user we expect the checkout link to point to Otto in a scenario where the CommerceConfiguration
        is active and the course mode is PROFESSIONAL.
        """
        if not is_anonymous:
            self.assert_enrollment_link_present(is_anonymous=is_anonymous)
        else:
            self.assertEqual(EcommerceService().is_enabled(AnonymousUser()), False)

    def test_user_groups(self):
        # depreciated function
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertEqual(views.user_groups(mock_user), [])

    def test_get_current_child(self):
        mock_xmodule = MagicMock()
        self.assertIsNone(views.get_current_child(mock_xmodule))

        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one', 'two', 'three']
        self.assertEqual(views.get_current_child(mock_xmodule), 'one')

        mock_xmodule.position = 2
        self.assertEqual(views.get_current_child(mock_xmodule), 'two')
        self.assertEqual(views.get_current_child(mock_xmodule, requested_child='first'), 'one')
        self.assertEqual(views.get_current_child(mock_xmodule, requested_child='last'), 'three')

        mock_xmodule.position = 3
        mock_xmodule.get_display_items.return_value = []
        self.assertIsNone(views.get_current_child(mock_xmodule))

    def test_get_redirect_url(self):
        self.assertIn(
            'activate_block_id',
            get_redirect_url(self.course_key, self.section.location),
        )

    def test_invalid_course_id(self):
        response = self.client.get('/courses/MITx/3.091X/')
        self.assertEqual(response.status_code, 404)

    def test_incomplete_course_id(self):
        response = self.client.get('/courses/MITx/')
        self.assertEqual(response.status_code, 404)

    def test_index_invalid_position(self):
        request_url = '/'.join([
            '/courses',
            unicode(self.course.id),
            'courseware',
            self.chapter.location.name,
            self.section.location.name,
            'f'
        ])
        self.assertTrue(self.client.login(username=self.user.username, password=self.password))
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 404)

    def test_unicode_handling_in_url(self):
        url_parts = [
            '/courses',
            unicode(self.course.id),
            'courseware',
            self.chapter.location.name,
            self.section.location.name,
            '1'
        ]
        self.assertTrue(self.client.login(username=self.user.username, password=self.password))
        for idx, val in enumerate(url_parts):
            url_parts_copy = url_parts[:]
            url_parts_copy[idx] = val + u'χ'
            request_url = '/'.join(url_parts_copy)
            response = self.client.get(request_url)
            self.assertEqual(response.status_code, 404)

    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=["USD", "$"])
    def test_get_cosmetic_display_price(self):
        """
        Check that get_cosmetic_display_price() returns the correct price given its inputs.
        """
        registration_price = 99
        self.course.cosmetic_display_price = 10
        # Since registration_price is set, it overrides the cosmetic_display_price and should be returned
        self.assertEqual(views.get_cosmetic_display_price(self.course, registration_price), "$99")

        registration_price = 0
        # Since registration_price is not set, cosmetic_display_price should be returned
        self.assertEqual(views.get_cosmetic_display_price(self.course, registration_price), "$10")

        self.course.cosmetic_display_price = 0
        # Since both prices are not set, there is no price, thus "Free"
        self.assertEqual(views.get_cosmetic_display_price(self.course, registration_price), "Free")

    def test_jump_to_invalid(self):
        # TODO add a test for invalid location
        # TODO add a test for no data *
        response = self.client.get(reverse('jump_to', args=['foo/bar/baz', 'baz']))
        self.assertEquals(response.status_code, 404)

    @unittest.skip
    def test_no_end_on_about_page(self):
        # Toy course has no course end date or about/end_date blob
        self.verify_end_date('edX/toy/TT_2012_Fall')

    @unittest.skip
    def test_no_end_about_blob(self):
        # test_end has a course end date, no end_date HTML blob
        self.verify_end_date("edX/test_end/2012_Fall", "Sep 17, 2015")

    @unittest.skip
    def test_about_blob_end_date(self):
        # test_about_blob_end_date has both a course end date and an end_date HTML blob.
        # HTML blob wins
        self.verify_end_date("edX/test_about_blob_end_date/2012_Fall", "Learning never ends")

    def verify_end_date(self, course_id, expected_end_text=None):
        """
        Visits the about page for `course_id` and tests that both the text "Classes End", as well
        as the specified `expected_end_text`, is present on the page.

        If `expected_end_text` is None, verifies that the about page *does not* contain the text
        "Classes End".
        """
        result = self.client.get(reverse('about_course', args=[unicode(course_id)]))
        if expected_end_text is not None:
            self.assertContains(result, "Classes End")
            self.assertContains(result, expected_end_text)
        else:
            self.assertNotContains(result, "Classes End")

    def test_submission_history_accepts_valid_ids(self):
        # log into a staff account
        admin = AdminFactory()

        self.assertTrue(self.client.login(username=admin.username, password='test'))

        url = reverse('submission_history', kwargs={
            'course_id': unicode(self.course_key),
            'student_username': 'dummy',
            'location': unicode(self.problem.location),
        })
        response = self.client.get(url)
        # Tests that we do not get an "Invalid x" response when passing correct arguments to view
        self.assertNotIn('Invalid', response.content)

    def test_submission_history_xss(self):
        # log into a staff account
        admin = AdminFactory()

        self.assertTrue(self.client.login(username=admin.username, password='test'))

        # try it with an existing user and a malicious location
        url = reverse('submission_history', kwargs={
            'course_id': unicode(self.course_key),
            'student_username': 'dummy',
            'location': '<script>alert("hello");</script>'
        })
        response = self.client.get(url)
        self.assertNotIn('<script>', response.content)

        # try it with a malicious user and a non-existent location
        url = reverse('submission_history', kwargs={
            'course_id': unicode(self.course_key),
            'student_username': '<script>alert("hello");</script>',
            'location': 'dummy'
        })
        response = self.client.get(url)
        self.assertNotIn('<script>', response.content)

    def test_submission_history_contents(self):
        # log into a staff account
        admin = AdminFactory.create()

        self.assertTrue(self.client.login(username=admin.username, password='test'))

        usage_key = self.course_key.make_usage_key('problem', 'test-history')
        state_client = DjangoXBlockUserStateClient(admin)

        # store state via the UserStateClient
        state_client.set(
            username=admin.username,
            block_key=usage_key,
            state={'field_a': 'x', 'field_b': 'y'}
        )

        set_score(admin.id, usage_key, 0, 3)

        state_client.set(
            username=admin.username,
            block_key=usage_key,
            state={'field_a': 'a', 'field_b': 'b'}
        )
        set_score(admin.id, usage_key, 3, 3)

        url = reverse('submission_history', kwargs={
            'course_id': unicode(self.course_key),
            'student_username': admin.username,
            'location': unicode(usage_key),
        })
        response = self.client.get(url)
        response_content = HTMLParser().unescape(response.content.decode('utf-8'))

        # We have update the state 4 times: twice to change content, and twice
        # to set the scores. We'll check that the identifying content from each is
        # displayed (but not the order), and also the indexes assigned in the output
        # #1 - #4

        self.assertIn('#1', response_content)
        self.assertIn(json.dumps({'field_a': 'a', 'field_b': 'b'}, sort_keys=True, indent=2), response_content)
        self.assertIn("Score: 0.0 / 3.0", response_content)
        self.assertIn(json.dumps({'field_a': 'x', 'field_b': 'y'}, sort_keys=True, indent=2), response_content)
        self.assertIn("Score: 3.0 / 3.0", response_content)
        self.assertIn('#4', response_content)

    @ddt.data(('America/New_York', -5),  # UTC - 5
              ('Asia/Pyongyang', 9),  # UTC + 9
              ('Europe/London', 0),  # UTC
              ('Canada/Yukon', -8),  # UTC - 8
              ('Europe/Moscow', 4))  # UTC + 3 + 1 for daylight savings
    @ddt.unpack
    @freeze_time('2012-01-01')
    def test_submission_history_timezone(self, timezone, hour_diff):
        with (override_settings(TIME_ZONE=timezone)):
            course = CourseFactory.create()
            course_key = course.id
            client = Client()
            admin = AdminFactory.create()
            self.assertTrue(client.login(username=admin.username, password='test'))
            state_client = DjangoXBlockUserStateClient(admin)
            usage_key = course_key.make_usage_key('problem', 'test-history')
            state_client.set(
                username=admin.username,
                block_key=usage_key,
                state={'field_a': 'x', 'field_b': 'y'}
            )
            url = reverse('submission_history', kwargs={
                'course_id': unicode(course_key),
                'student_username': admin.username,
                'location': unicode(usage_key),
            })
            response = client.get(url)
            response_content = HTMLParser().unescape(response.content)
            expected_time = datetime.now() + timedelta(hours=hour_diff)
            expected_tz = expected_time.strftime('%Z')
            self.assertIn(expected_tz, response_content)
            self.assertIn(str(expected_time), response_content)

    def _email_opt_in_checkbox(self, response, org_name_string=None):
        """Check if the email opt-in checkbox appears in the response content."""
        checkbox_html = '<input id="email-opt-in" type="checkbox" name="opt-in" class="email-opt-in" value="true" checked>'
        if org_name_string:
            # Verify that the email opt-in checkbox appears, and that the expected
            # organization name is displayed.
            self.assertContains(response, checkbox_html, html=True)
            self.assertContains(response, org_name_string)
        else:
            # Verify that the email opt-in checkbox does not appear
            self.assertNotContains(response, checkbox_html, html=True)

    def test_financial_assistance_page(self):
        url = reverse('financial_assistance')
        response = self.client.get(url)
        # This is a static page, so just assert that it is returned correctly
        self.assertEqual(response.status_code, 200)
        self.assertIn('Financial Assistance Application', response.content)

    def test_financial_assistance_form(self):
        non_verified_course = CourseFactory.create().id
        verified_course_verified_track = CourseFactory.create().id
        verified_course_audit_track = CourseFactory.create().id
        verified_course_deadline_passed = CourseFactory.create().id
        unenrolled_course = CourseFactory.create().id

        enrollments = (
            (non_verified_course, CourseMode.AUDIT, None),
            (verified_course_verified_track, CourseMode.VERIFIED, None),
            (verified_course_audit_track, CourseMode.AUDIT, None),
            (verified_course_deadline_passed, CourseMode.AUDIT, datetime.now(UTC) - timedelta(days=1))
        )
        for course, mode, expiration in enrollments:
            CourseModeFactory.create(mode_slug=CourseMode.AUDIT, course_id=course)
            if course != non_verified_course:
                CourseModeFactory.create(
                    mode_slug=CourseMode.VERIFIED,
                    course_id=course,
                    expiration_datetime=expiration
                )
            CourseEnrollmentFactory(course_id=course, user=self.user, mode=mode)

        url = reverse('financial_assistance_form')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Ensure that the user can only apply for assistance in
        # courses which have a verified mode which hasn't expired yet,
        # where the user is not already enrolled in verified mode
        self.assertIn(str(verified_course_audit_track), response.content)
        for course in (
                non_verified_course,
                verified_course_verified_track,
                verified_course_deadline_passed,
                unenrolled_course
        ):
            self.assertNotIn(str(course), response.content)

    def _submit_financial_assistance_form(self, data):
        """Submit a financial assistance request."""
        url = reverse('submit_financial_assistance_request')
        return self.client.post(url, json.dumps(data), content_type='application/json')

    @patch.object(views, '_record_feedback_in_zendesk')
    def test_submit_financial_assistance_request(self, mock_record_feedback):
        username = self.user.username
        course = unicode(self.course_key)
        legal_name = 'Jesse Pinkman'
        country = 'United States'
        income = '1234567890'
        reason_for_applying = "It's just basic chemistry, yo."
        goals = "I don't know if it even matters, but... work with my hands, I guess."
        effort = "I'm done, okay? You just give me my money, and you and I, we're done."
        data = {
            'username': username,
            'course': course,
            'name': legal_name,
            'email': self.user.email,
            'country': country,
            'income': income,
            'reason_for_applying': reason_for_applying,
            'goals': goals,
            'effort': effort,
            'mktg-permission': False,
        }
        response = self._submit_financial_assistance_form(data)
        self.assertEqual(response.status_code, 204)

        __, __, ticket_subject, __, tags, additional_info = mock_record_feedback.call_args[0]
        mocked_kwargs = mock_record_feedback.call_args[1]
        group_name = mocked_kwargs['group_name']
        require_update = mocked_kwargs['require_update']
        private_comment = '\n'.join(additional_info.values())
        for info in (country, income, reason_for_applying, goals, effort, username, legal_name, course):
            self.assertIn(info, private_comment)

        self.assertEqual(additional_info['Allowed for marketing purposes'], 'No')

        self.assertEqual(
            ticket_subject,
            u'Financial assistance request for learner {username} in course {course}'.format(
                username=username,
                course=self.course.display_name
            )
        )
        self.assertDictContainsSubset({'course_id': course}, tags)
        self.assertIn('Client IP', additional_info)
        self.assertEqual(group_name, 'Financial Assistance')
        self.assertTrue(require_update)

    @patch.object(views, '_record_feedback_in_zendesk', return_value=False)
    def test_zendesk_submission_failed(self, _mock_record_feedback):
        response = self._submit_financial_assistance_form({
            'username': self.user.username,
            'course': unicode(self.course.id),
            'name': '',
            'email': '',
            'country': '',
            'income': '',
            'reason_for_applying': '',
            'goals': '',
            'effort': '',
            'mktg-permission': False,
        })
        self.assertEqual(response.status_code, 500)

    @ddt.data(
        ({}, 400),
        ({'username': 'wwhite'}, 403),
        ({'username': 'dummy', 'course': 'bad course ID'}, 400)
    )
    @ddt.unpack
    def test_submit_financial_assistance_errors(self, data, status):
        response = self._submit_financial_assistance_form(data)
        self.assertEqual(response.status_code, status)

    def test_financial_assistance_login_required(self):
        for url in (
                reverse('financial_assistance'),
                reverse('financial_assistance_form'),
                reverse('submit_financial_assistance_request')
        ):
            self.client.logout()
            response = self.client.get(url)
            self.assertRedirects(response, reverse('signin_user') + '?next=' + url)

    def test_bypass_course_info(self):
        course_id = unicode(self.course_key)

        self.assertFalse(self.course.bypass_home)

        response = self.client.get(reverse('info', args=[course_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('info', args=[course_id]), HTTP_REFERER=reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        self.course.bypass_home = True
        self.store.update_item(self.course, self.user.id)  # pylint: disable=no-member
        self.assertTrue(self.course.bypass_home)

        response = self.client.get(reverse('info', args=[course_id]), HTTP_REFERER=reverse('dashboard'))

        self.assertRedirects(response, reverse('courseware', args=[course_id]), fetch_redirect_response=False)

        response = self.client.get(reverse('info', args=[course_id]), HTTP_REFERER='foo')
        self.assertEqual(response.status_code, 200)

    def test_accordion(self):
        request = RequestFactory().get('foo')
        request.user = self.user
        table_of_contents = toc_for_course(
            request.user,
            request,
            self.course,
            unicode(self.course.get_children()[0].scope_ids.usage_id),
            None,
            None
        )

        # removes newlines and whitespace from the returned view string
        view = ''.join(render_accordion(request, self.course, table_of_contents['chapters'], 'en').split())
        # the course id unicode is re-encoded here because the quote function does not accept unicode
        course_id = quote(unicode(self.course.id).encode("utf-8"))

        self.assertIn(
            u'href="/courses/{}/courseware/Chapter_1/Sequential_1/"><pclass="accordion-display-name">Sequential1</p>'
            .format(course_id.decode("utf-8")),
            view
        )

        self.assertIn(
            u'href="/courses/{}/courseware/Chapter_1/Sequential_2/"><pclass="accordion-display-name">Sequential2</p>'
            .format(course_id.decode("utf-8")),
            view
        )


@attr(shard=1)
# setting TIME_ZONE_DISPLAYED_FOR_DEADLINES explicitly
@override_settings(TIME_ZONE_DISPLAYED_FOR_DEADLINES="UTC")
class BaseDueDateTests(ModuleStoreTestCase):
    """
    Base class that verifies that due dates are rendered correctly on a page
    """
    __test__ = False

    def get_response(self, course):
        """Return the rendered text for the page to be verified"""
        raise NotImplementedError

    def set_up_course(self, **course_kwargs):
        """
        Create a stock course with a specific due date.

        :param course_kwargs: All kwargs are passed to through to the :class:`CourseFactory`
        """
        course = CourseFactory.create(**course_kwargs)
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        section = ItemFactory.create(
            category='sequential',
            parent_location=chapter.location,
            due=datetime(2013, 9, 18, 11, 30, 00)
        )
        vertical = ItemFactory.create(category='vertical', parent_location=section.location)
        ItemFactory.create(category='problem', parent_location=vertical.location)

        course = modulestore().get_course(course.id)
        self.assertIsNotNone(course.get_children()[0].get_children()[0].due)
        CourseEnrollmentFactory(user=self.user, course_id=course.id)
        return course

    def setUp(self):
        super(BaseDueDateTests, self).setUp()
        self.user = UserFactory.create()
        self.assertTrue(self.client.login(username=self.user.username, password='test'))

        self.time_with_tz = "due Sep 18, 2013 at 11:30 UTC"
        self.time_without_tz = "due Sep 18, 2013 at 11:30"

    def test_backwards_compatability(self):
        # The test course being used has show_timezone = False in the policy file
        # (and no due_date_display_format set). This is to test our backwards compatibility--
        # in course_module's init method, the date_display_format will be set accordingly to
        # remove the timezone.
        course = self.set_up_course(due_date_display_format=None, show_timezone=False)
        response = self.get_response(course)
        self.assertContains(response, self.time_without_tz)
        self.assertNotContains(response, self.time_with_tz)
        # Test that show_timezone has been cleared (which means you get the default value of True).
        self.assertTrue(course.show_timezone)

    def test_defaults(self):
        course = self.set_up_course()
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)

    def test_format_none(self):
        # Same for setting the due date to None
        course = self.set_up_course(due_date_display_format=None)
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)

    def test_format_plain_text(self):
        # plain text due date
        course = self.set_up_course(due_date_display_format="foobar")
        response = self.get_response(course)
        self.assertNotContains(response, self.time_with_tz)
        self.assertContains(response, "due foobar")

    def test_format_date(self):
        # due date with no time
        course = self.set_up_course(due_date_display_format=u"%b %d %y")
        response = self.get_response(course)
        self.assertNotContains(response, self.time_with_tz)
        self.assertContains(response, "due Sep 18 13")

    def test_format_hidden(self):
        # hide due date completely
        course = self.set_up_course(due_date_display_format=u"")
        response = self.get_response(course)
        self.assertNotContains(response, "due ")

    def test_format_invalid(self):
        # improperly formatted due_date_display_format falls through to default
        # (value of show_timezone does not matter-- setting to False to make that clear).
        course = self.set_up_course(due_date_display_format=u"%%%", show_timezone=False)
        response = self.get_response(course)
        self.assertNotContains(response, "%%%")
        self.assertContains(response, self.time_with_tz)


class TestProgressDueDate(BaseDueDateTests):
    """
    Test that the progress page displays due dates correctly
    """
    __test__ = True

    def get_response(self, course):
        """ Returns the HTML for the progress page """
        return self.client.get(reverse('progress', args=[unicode(course.id)]))


class TestAccordionDueDate(BaseDueDateTests):
    """
    Test that the accordion page displays due dates correctly
    """
    __test__ = True

    def get_response(self, course):
        """ Returns the HTML for the accordion """
        return self.client.get(reverse('courseware', args=[unicode(course.id)]), follow=True)


@attr(shard=1)
class StartDateTests(ModuleStoreTestCase):
    """
    Test that start dates are properly localized and displayed on the student
    dashboard.
    """

    def setUp(self):
        super(StartDateTests, self).setUp()
        self.user = UserFactory.create()

    def set_up_course(self):
        """
        Create a stock course with a specific due date.

        :param course_kwargs: All kwargs are passed to through to the :class:`CourseFactory`
        """
        course = CourseFactory.create(start=datetime(2013, 9, 16, 7, 17, 28))
        course = modulestore().get_course(course.id)
        return course

    def get_about_response(self, course_key):
        """
        Get the text of the /about page for the course.
        """
        return self.client.get(reverse('about_course', args=[unicode(course_key)]))

    @patch('util.date_utils.pgettext', fake_pgettext(translations={
        ("abbreviated month name", "Sep"): "SEPTEMBER",
    }))
    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "SHORT_DATE_FORMAT": "%Y-%b-%d",
    }))
    def test_format_localized_in_studio_course(self):
        course = self.set_up_course()
        response = self.get_about_response(course.id)
        # The start date is set in the set_up_course function above.
        self.assertContains(response, "2013-SEPTEMBER-16")

    @patch('util.date_utils.pgettext', fake_pgettext(translations={
        ("abbreviated month name", "Jul"): "JULY",
    }))
    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "SHORT_DATE_FORMAT": "%Y-%b-%d",
    }))
    @unittest.skip
    def test_format_localized_in_xml_course(self):
        response = self.get_about_response(SlashSeparatedCourseKey('edX', 'toy', 'TT_2012_Fall'))
        # The start date is set in common/test/data/two_toys/policies/TT_2012_Fall/policy.json
        self.assertContains(response, "2015-JULY-17")


# pylint: disable=protected-access, no-member
@attr(shard=1)
@ddt.ddt
class ProgressPageTests(ModuleStoreTestCase):
    """
    Tests that verify that the progress page works correctly.
    """

    ENABLED_CACHES = ['default', 'mongo_modulestore_inheritance', 'loc_cache']

    def setUp(self):
        super(ProgressPageTests, self).setUp()
        self.user = UserFactory.create()
        self.assertTrue(self.client.login(username=self.user.username, password='test'))

        self.setup_course()

    def setup_course(self, **options):
        """Create the test course."""
        course = CourseFactory.create(
            start=datetime(2013, 9, 16, 7, 17, 28),
            grade_cutoffs={u'çü†øƒƒ': 0.75, 'Pass': 0.5},
            **options
        )

        self.course = modulestore().get_course(course.id)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.HONOR)

        self.chapter = ItemFactory.create(category='chapter', parent_location=self.course.location)
        self.section = ItemFactory.create(category='sequential', parent_location=self.chapter.location)
        self.vertical = ItemFactory.create(category='vertical', parent_location=self.section.location)

    def _get_progress_page(self, expected_status_code=200):
        """
        Gets the progress page for the user in the course.
        """
        resp = self.client.get(
            reverse('progress', args=[unicode(self.course.id)])
        )
        self.assertEqual(resp.status_code, expected_status_code)
        return resp

    def _get_student_progress_page(self, expected_status_code=200):
        """
        Gets the progress page for the user in the course.
        """
        resp = self.client.get(
            reverse('student_progress', args=[unicode(self.course.id), self.user.id])
        )
        self.assertEqual(resp.status_code, expected_status_code)
        return resp

    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    def test_progress_page_xss_prevent(self, malicious_code):
        """
        Test that XSS attack is prevented
        """
        resp = self._get_student_progress_page()
        # Test that malicious code does not appear in html
        self.assertNotIn(malicious_code, resp.content)

    def test_pure_ungraded_xblock(self):
        ItemFactory.create(category='acid', parent_location=self.vertical.location)
        self._get_progress_page()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_student_progress_with_valid_and_invalid_id(self, default_store):
        """
         Check that invalid 'student_id' raises Http404 for both old mongo and
         split mongo courses.
        """

        # Create new course with respect to 'default_store'
        # Enroll student into course
        self.course = CourseFactory.create(default_store=default_store)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.HONOR)

        # Invalid Student Ids (Integer and Non-int)
        invalid_student_ids = [
            991021,
            'azU3N_8$',
        ]
        for invalid_id in invalid_student_ids:

            resp = self.client.get(
                reverse('student_progress', args=[unicode(self.course.id), invalid_id])
            )
            self.assertEquals(resp.status_code, 404)

        # Assert that valid 'student_id' returns 200 status
        self._get_student_progress_page()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_unenrolled_student_progress_for_credit_course(self, default_store):
        """
         Test that student progress page does not break while checking for an unenrolled student.

         Scenario: When instructor checks the progress of a student who is not enrolled in credit course.
         It should return 200 response.
        """
        # Create a new course, a user which will not be enrolled in course, admin user for staff access
        course = CourseFactory.create(default_store=default_store)
        not_enrolled_user = UserFactory.create()
        admin = AdminFactory.create()
        self.assertTrue(self.client.login(username=admin.username, password='test'))

        # Create and enable Credit course
        CreditCourse.objects.create(course_key=course.id, enabled=True)

        # Configure a credit provider for the course
        CreditProvider.objects.create(
            provider_id="ASU",
            enable_integration=True,
            provider_url="https://credit.example.com/request"
        )

        requirements = [{
            "namespace": "grade",
            "name": "grade",
            "display_name": "Grade",
            "criteria": {"min_grade": 0.52},
        }]
        # Add a single credit requirement (final grade)
        set_credit_requirements(course.id, requirements)

        self._get_student_progress_page()

    def test_non_ascii_grade_cutoffs(self):
        self._get_progress_page()

    def test_generate_cert_config(self):

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []}),
    )
    def test_view_certificate_link(self):
        """
        If certificate web view is enabled then certificate web view button should appear for user who certificate is
        available/generated
        """
        certificate = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            download_url="http://www.example.com/certificate.pdf",
            mode='honor'
        )

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)

        # Course certificate configurations
        certificates = [
            {
                'id': 1,
                'name': 'Name 1',
                'description': 'Description 1',
                'course_title': 'course_title_1',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        resp = self._get_progress_page()
        self.assertContains(resp, u"View Certificate")

        self.assertContains(resp, u"You can keep working for a higher grade")
        cert_url = certs_api.get_certificate_url(course_id=self.course.id, uuid=certificate.verify_uuid)
        self.assertContains(resp, cert_url)

        # when course certificate is not active
        certificates[0]['is_active'] = False
        self.store.update_item(self.course, self.user.id)

        resp = self._get_progress_page()
        self.assertNotContains(resp, u"View Your Certificate")
        self.assertNotContains(resp, u"You can now view your certificate")
        self.assertContains(resp, "working on it...")
        self.assertContains(resp, "creating your certificate")

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []})
    )
    def test_view_certificate_link_hidden(self):
        """
        If certificate web view is disabled then certificate web view button should not appear for user who certificate
        is available/generated
        """
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            download_url="http://www.example.com/certificate.pdf",
            mode='honor'
        )

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)

        resp = self._get_progress_page()
        self.assertContains(resp, u"Download Your Certificate")

    @ddt.data(
        *itertools.product((True, False), (True, False))
    )
    @ddt.unpack
    def test_progress_queries_paced_courses(self, self_paced, self_paced_enabled):
        """Test that query counts remain the same for self-paced and instructor-paced courses."""
        SelfPacedConfiguration(enabled=self_paced_enabled).save()
        self.setup_course(self_paced=self_paced)
        with self.assertNumQueries(44), check_mongo_calls(4):
            self._get_progress_page()

    def test_progress_queries(self):
        self.setup_course()
        with self.assertNumQueries(44), check_mongo_calls(4):
            self._get_progress_page()

        # subsequent accesses to the progress page require fewer queries.
        for _ in range(2):
            with self.assertNumQueries(17), check_mongo_calls(4):
                self._get_progress_page()

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []})
    )
    @ddt.data(
        *itertools.product(
            (
                CourseMode.AUDIT,
                CourseMode.HONOR,
                CourseMode.VERIFIED,
                CourseMode.PROFESSIONAL,
                CourseMode.NO_ID_PROFESSIONAL_MODE,
                CourseMode.CREDIT_MODE
            ),
            (True, False)
        )
    )
    @ddt.unpack
    def test_show_certificate_request_button(self, course_mode, user_verified):
        """Verify that the Request Certificate is not displayed in audit mode."""
        CertificateGenerationConfiguration(enabled=True).save()
        certs_api.set_cert_generation_enabled(self.course.id, True)
        CourseEnrollment.enroll(self.user, self.course.id, mode=course_mode)
        with patch(
            'lms.djangoapps.verify_student.models.SoftwareSecurePhotoVerification.user_is_verified'
        ) as user_verify:
            user_verify.return_value = user_verified
            resp = self.client.get(
                reverse('progress', args=[unicode(self.course.id)])
            )

            cert_button_hidden = course_mode is CourseMode.AUDIT or \
                course_mode in CourseMode.VERIFIED_MODES and not user_verified

            self.assertEqual(
                cert_button_hidden,
                'Request Certificate' not in resp.content
            )

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []})
    )
    def test_page_with_invalidated_certificate_with_html_view(self):
        """
        Verify that for html certs if certificate is marked as invalidated than
        re-generate button should not appear on progress page.
        """
        generated_certificate = self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )

        # Course certificate configurations
        certificates = [
            {
                'id': 1,
                'name': 'dummy',
                'description': 'dummy description',
                'course_title': 'dummy title',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        resp = self._get_progress_page()
        self.assertContains(resp, u"View Certificate")
        self.assert_invalidate_certificate(generated_certificate)

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []})
    )
    def test_page_with_invalidated_certificate_with_pdf(self):
        """
        Verify that for pdf certs if certificate is marked as invalidated than
        re-generate button should not appear on progress page.
        """
        generated_certificate = self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )

        resp = self._get_progress_page()
        self.assertContains(resp, u'Download Your Certificate')
        self.assert_invalidate_certificate(generated_certificate)

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': []})
    )
    def test_message_for_audit_mode(self):
        """ Verify that message appears on progress page, if learner is enrolled
         in audit mode.
        """
        user = UserFactory.create()
        self.assertTrue(self.client.login(username=user.username, password='test'))
        CourseEnrollmentFactory(user=user, course_id=self.course.id, mode=CourseMode.AUDIT)
        response = self._get_progress_page()

        self.assertContains(
            response,
            u'You are enrolled in the audit track for this course. The audit track does not include a certificate.'
        )

    def test_invalidated_cert_data(self):
        """
        Verify that invalidated cert data is returned if cert is invalidated.
        """
        generated_certificate = self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )

        CertificateInvalidationFactory.create(
            generated_certificate=generated_certificate,
            invalidated_by=self.user
        )
        # Invalidate user certificate
        generated_certificate.invalidate()
        response = views._get_cert_data(self.user, self.course, self.course.id, True, CourseMode.HONOR)
        self.assertEqual(response.cert_status, 'invalidated')
        self.assertEqual(response.title, 'Your certificate has been invalidated')

    def test_downloadable_get_cert_data(self):
        """
        Verify that downloadable cert data is returned if cert is downloadable.
        """
        self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )
        with patch('certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(is_downloadable=True)):
            response = views._get_cert_data(self.user, self.course, self.course.id, True, CourseMode.HONOR)

        self.assertEqual(response.cert_status, 'downloadable')
        self.assertEqual(response.title, 'Your certificate is available')

    def test_generating_get_cert_data(self):
        """
        Verify that generating cert data is returned if cert is generating.
        """
        self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )
        with patch('certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(is_generating=True)):
            response = views._get_cert_data(self.user, self.course, self.course.id, True, CourseMode.HONOR)

        self.assertEqual(response.cert_status, 'generating')
        self.assertEqual(response.title, "We're working on it...")

    def test_unverified_get_cert_data(self):
        """
        Verify that unverified cert data is returned if cert is unverified.
        """
        self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )
        with patch('certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(is_unverified=True)):
            response = views._get_cert_data(self.user, self.course, self.course.id, True, CourseMode.HONOR)

        self.assertEqual(response.cert_status, 'unverified')
        self.assertEqual(response.title, "Certificate unavailable")

    def test_request_get_cert_data(self):
        """
        Verify that requested cert data is returned if cert is to be requested.
        """
        self.generate_certificate(
            "http://www.example.com/certificate.pdf", "honor"
        )
        with patch('certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status()):
            response = views._get_cert_data(self.user, self.course, self.course.id, True, CourseMode.HONOR)

        self.assertEqual(response.cert_status, 'requesting')
        self.assertEqual(response.title, "Congratulations, you qualified for a certificate!")

    def assert_invalidate_certificate(self, certificate):
        """ Dry method to mark certificate as invalid. And assert the response. """
        CertificateInvalidationFactory.create(
            generated_certificate=certificate,
            invalidated_by=self.user
        )
        # Invalidate user certificate
        certificate.invalidate()
        resp = self._get_progress_page()

        self.assertNotContains(resp, u'Request Certificate')
        self.assertContains(resp, u'Your certificate has been invalidated')
        self.assertContains(resp, u'Please contact your course team if you have any questions.')
        self.assertNotContains(resp, u'View Your Certificate')
        self.assertNotContains(resp, u'Download Your Certificate')

    def generate_certificate(self, url, mode):
        """ Dry method to generate certificate. """

        generated_certificate = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            download_url=url,
            mode=mode
        )
        CertificateGenerationConfiguration(enabled=True).save()
        certs_api.set_cert_generation_enabled(self.course.id, True)
        return generated_certificate

    def mock_certificate_downloadable_status(
            self, is_downloadable=False, is_generating=False, is_unverified=False, uuid=None, download_url=None
    ):
        """Dry method to mock certificate downloadable status response."""
        return {
            'is_downloadable': is_downloadable,
            'is_generating': is_generating,
            'is_unverified': is_unverified,
            'download_url': uuid,
            'uuid': download_url,
        }


@attr(shard=1)
class VerifyCourseKeyDecoratorTests(TestCase):
    """
    Tests for the ensure_valid_course_key decorator.
    """

    def setUp(self):
        super(VerifyCourseKeyDecoratorTests, self).setUp()

        self.request = RequestFactory().get("foo")
        self.valid_course_id = "edX/test/1"
        self.invalid_course_id = "edX/"

    def test_decorator_with_valid_course_id(self):
        mocked_view = create_autospec(views.course_about)
        view_function = ensure_valid_course_key(mocked_view)
        view_function(self.request, course_id=self.valid_course_id)
        self.assertTrue(mocked_view.called)

    def test_decorator_with_invalid_course_id(self):
        mocked_view = create_autospec(views.course_about)
        view_function = ensure_valid_course_key(mocked_view)
        self.assertRaises(Http404, view_function, self.request, course_id=self.invalid_course_id)
        self.assertFalse(mocked_view.called)


@attr(shard=1)
class IsCoursePassedTests(ModuleStoreTestCase):
    """
    Tests for the is_course_passed helper function
    """

    SUCCESS_CUTOFF = 0.5

    def setUp(self):
        super(IsCoursePassedTests, self).setUp()

        self.student = UserFactory()
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course',
            grade_cutoffs={'cutoff': 0.75, 'Pass': self.SUCCESS_CUTOFF}
        )
        self.request = RequestFactory()
        self.request.user = self.student

    def test_user_fails_if_not_clear_exam(self):
        # If user has not grade then false will return
        self.assertFalse(views.is_course_passed(self.course, None, self.student, self.request))

    @patch('lms.djangoapps.grades.new.course_grade.CourseGrade.summary', PropertyMock(return_value={'percent': 0.9}))
    def test_user_pass_if_percent_appears_above_passing_point(self):
        # Mocking the grades.grade
        # If user has above passing marks then True will return
        self.assertTrue(views.is_course_passed(self.course, None, self.student, self.request))

    @patch('lms.djangoapps.grades.new.course_grade.CourseGrade.summary', PropertyMock(return_value={'percent': 0.2}))
    def test_user_fail_if_percent_appears_below_passing_point(self):
        # Mocking the grades.grade
        # If user has below passing marks then False will return
        self.assertFalse(views.is_course_passed(self.course, None, self.student, self.request))

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'percent': SUCCESS_CUTOFF})
    )
    def test_user_with_passing_marks_and_achieved_marks_equal(self):
        # Mocking the grades.grade
        # If user's achieved passing marks are equal to the required passing
        # marks then it will return True
        self.assertTrue(views.is_course_passed(self.course, None, self.student, self.request))


@attr(shard=1)
class GenerateUserCertTests(ModuleStoreTestCase):
    """
    Tests for the view function Generated User Certs
    """

    def setUp(self):
        super(GenerateUserCertTests, self).setUp()

        self.student = UserFactory(username='dummy', password='123456', email='test@mit.edu')
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course',
            grade_cutoffs={'cutoff': 0.75, 'Pass': 0.5}
        )
        self.enrollment = CourseEnrollment.enroll(self.student, self.course.id, mode='honor')
        self.assertTrue(self.client.login(username=self.student, password='123456'))
        self.url = reverse('generate_user_cert', kwargs={'course_id': unicode(self.course.id)})

    def test_user_with_out_passing_grades(self):
        # If user has no grading then json will return failed message and badrequest code
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)
        self.assertIn("Your certificate will be available when you pass the course.", resp.content)

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75})
    )
    @override_settings(CERT_QUEUE='certificates', LMS_SEGMENT_KEY="foobar")
    def test_user_with_passing_grade(self):
        # If user has above passing grading then json will return cert generating message and
        # status valid code
        # mocking xqueue and analytics

        analytics_patcher = patch('courseware.views.views.analytics')
        mock_tracker = analytics_patcher.start()
        self.addCleanup(analytics_patcher.stop)

        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")
            resp = self.client.post(self.url)
            self.assertEqual(resp.status_code, 200)

            # Verify Google Analytics event fired after generating certificate
            mock_tracker.track.assert_called_once_with(  # pylint: disable=no-member
                self.student.id,  # pylint: disable=no-member
                'edx.bi.user.certificate.generate',
                {
                    'category': 'certificates',
                    'label': unicode(self.course.id)
                },

                context={
                    'ip': '127.0.0.1',
                    'Google Analytics': {'clientId': None}
                }
            )
            mock_tracker.reset_mock()

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75})
    )
    def test_user_with_passing_existing_generating_cert(self):
        # If user has passing grade but also has existing generating cert
        # then json will return cert generating message with bad request code
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)
        self.assertIn("Certificate is being created.", resp.content)

    @patch(
        'lms.djangoapps.grades.new.course_grade.CourseGrade.summary',
        PropertyMock(return_value={'grade': 'Pass', 'percent': 0.75})
    )
    @override_settings(CERT_QUEUE='certificates', LMS_SEGMENT_KEY="foobar")
    def test_user_with_passing_existing_downloadable_cert(self):
        # If user has already downloadable certificate
        # then json will return cert generating message with bad request code

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)
        self.assertIn("Certificate has already been created.", resp.content)

    def test_user_with_non_existing_course(self):
        # If try to access a course with valid key pattern then it will return
        # bad request code with course is not valid message
        resp = self.client.post('/courses/def/abc/in_valid/generate_user_cert')
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)
        self.assertIn("Course is not valid", resp.content)

    def test_user_with_invalid_course_id(self):
        # If try to access a course with invalid key pattern then 404 will return
        resp = self.client.post('/courses/def/generate_user_cert')
        self.assertEqual(resp.status_code, 404)

    def test_user_without_login_return_error(self):
        # If user try to access without login should see a bad request status code with message
        self.client.logout()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)
        self.assertIn(u"You must be signed in to {platform_name} to create a certificate.".format(
            platform_name=settings.PLATFORM_NAME
        ), resp.content.decode('utf-8'))


class ActivateIDCheckerBlock(XBlock):
    """
    XBlock for checking for an activate_block_id entry in the render context.
    """
    # We don't need actual children to test this.
    has_children = False

    def student_view(self, context):
        """
        A student view that displays the activate_block_id context variable.
        """
        result = Fragment()
        if 'activate_block_id' in context:
            result.add_content(u"Activate Block ID: {block_id}</p>".format(block_id=context['activate_block_id']))
        return result


class ViewCheckerBlock(XBlock):
    """
    XBlock for testing user state in views.
    """
    has_children = True
    state = String(scope=Scope.user_state)

    def student_view(self, context):  # pylint: disable=unused-argument
        """
        A student_view that asserts that the ``state`` field for this block
        matches the block's usage_id.
        """
        msg = "{} != {}".format(self.state, self.scope_ids.usage_id)
        assert self.state == unicode(self.scope_ids.usage_id), msg
        fragments = self.runtime.render_children(self)
        result = Fragment(
            content=u"<p>ViewCheckerPassed: {}</p>\n{}".format(
                unicode(self.scope_ids.usage_id),
                "\n".join(fragment.content for fragment in fragments),
            )
        )
        return result


@attr(shard=1)
@ddt.ddt
class TestIndexView(ModuleStoreTestCase):
    """
    Tests of the courseware.views.index view.
    """

    @XBlock.register_temp_plugin(ViewCheckerBlock, 'view_checker')
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_student_state(self, default_store):
        """
        Verify that saved student state is loaded for xblocks rendered in the index view.
        """
        user = UserFactory()

        with modulestore().default_store(default_store):
            course = CourseFactory.create()
            chapter = ItemFactory.create(parent=course, category='chapter')
            section = ItemFactory.create(parent=chapter, category='view_checker', display_name="Sequence Checker")
            vertical = ItemFactory.create(parent=section, category='view_checker', display_name="Vertical Checker")
            block = ItemFactory.create(parent=vertical, category='view_checker', display_name="Block Checker")

        for item in (section, vertical, block):
            StudentModuleFactory.create(
                student=user,
                course_id=course.id,
                module_state_key=item.scope_ids.usage_id,
                state=json.dumps({'state': unicode(item.scope_ids.usage_id)})
            )

        CourseEnrollmentFactory(user=user, course_id=course.id)

        self.assertTrue(self.client.login(username=user.username, password='test'))
        response = self.client.get(
            reverse(
                'courseware_section',
                kwargs={
                    'course_id': unicode(course.id),
                    'chapter': chapter.url_name,
                    'section': section.url_name,
                }
            )
        )

        # Trigger the assertions embedded in the ViewCheckerBlocks
        self.assertEquals(response.content.count("ViewCheckerPassed"), 3)

    @XBlock.register_temp_plugin(ActivateIDCheckerBlock, 'id_checker')
    def test_activate_block_id(self):
        user = UserFactory()

        course = CourseFactory.create()
        chapter = ItemFactory.create(parent=course, category='chapter')
        section = ItemFactory.create(parent=chapter, category='sequential', display_name="Sequence")
        vertical = ItemFactory.create(parent=section, category='vertical', display_name="Vertical")
        ItemFactory.create(parent=vertical, category='id_checker', display_name="ID Checker")

        CourseEnrollmentFactory(user=user, course_id=course.id)

        self.assertTrue(self.client.login(username=user.username, password='test'))
        response = self.client.get(
            reverse(
                'courseware_section',
                kwargs={
                    'course_id': unicode(course.id),
                    'chapter': chapter.url_name,
                    'section': section.url_name,
                }
            ) + '?activate_block_id=test_block_id'
        )
        self.assertIn("Activate Block ID: test_block_id", response.content)


@ddt.ddt
class TestIndexViewWithVerticalPositions(ModuleStoreTestCase):
    """
    Test the index view to handle vertical positions. Confirms that first position is loaded
    if input position is non-positive or greater than number of positions available.
    """

    def setUp(self):
        """
        Set up initial test data
        """
        super(TestIndexViewWithVerticalPositions, self).setUp()

        self.user = UserFactory()

        # create course with 3 positions
        self.course = CourseFactory.create()
        self.chapter = ItemFactory.create(parent=self.course, category='chapter')
        self.section = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Sequence")
        ItemFactory.create(parent=self.section, category='vertical', display_name="Vertical1")
        ItemFactory.create(parent=self.section, category='vertical', display_name="Vertical2")
        ItemFactory.create(parent=self.section, category='vertical', display_name="Vertical3")

        self.client.login(username=self.user, password='test')
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

    def _get_course_vertical_by_position(self, input_position):
        """
        Returns client response to input position.
        """
        return self.client.get(
            reverse(
                'courseware_position',
                kwargs={
                    'course_id': unicode(self.course.id),
                    'chapter': self.chapter.url_name,
                    'section': self.section.url_name,
                    'position': input_position,
                }
            )
        )

    def _assert_correct_position(self, response, expected_position):
        """
        Asserts that the expected position and the position in the response are the same
        """
        self.assertIn('data-position="{}"'.format(expected_position), response.content)

    @ddt.data(("-1", 1), ("0", 1), ("-0", 1), ("2", 2), ("5", 1))
    @ddt.unpack
    def test_vertical_positions(self, input_position, expected_position):
        """
        Tests the following cases:

        * Load first position when negative position inputted.
        * Load first position when 0/-0 position inputted.
        * Load given position when 0 < input_position <= num_positions_available.
        * Load first position when positive position > num_positions_available.
        """
        resp = self._get_course_vertical_by_position(input_position)
        self._assert_correct_position(resp, expected_position)


class TestIndexViewWithGating(ModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Test the index view for a course with gated content
    """

    def setUp(self):
        """
        Set up the initial test data
        """
        super(TestIndexViewWithGating, self).setUp()

        self.user = UserFactory()
        self.course = CourseFactory.create()
        self.course.enable_subsection_gating = True
        self.course.save()
        self.store.update_item(self.course, 0)
        self.chapter = ItemFactory.create(parent=self.course, category="chapter", display_name="Chapter")
        self.open_seq = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Open Sequential")
        ItemFactory.create(parent=self.open_seq, category='problem', display_name="Problem 1")
        self.gated_seq = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Gated Sequential")
        ItemFactory.create(parent=self.gated_seq, category='problem', display_name="Problem 2")
        gating_api.add_prerequisite(self.course.id, self.open_seq.location)
        gating_api.set_required_content(self.course.id, self.gated_seq.location, self.open_seq.location, 100)

        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

    def test_index_with_gated_sequential(self):
        """
        Test index view with a gated sequential raises Http404
        """
        self.assertTrue(self.client.login(username=self.user.username, password='test'))
        response = self.client.get(
            reverse(
                'courseware_section',
                kwargs={
                    'course_id': unicode(self.course.id),
                    'chapter': self.chapter.url_name,
                    'section': self.gated_seq.url_name,
                }
            )
        )

        self.assertEquals(response.status_code, 404)


class TestRenderXBlock(RenderXBlockTestMixin, ModuleStoreTestCase):
    """
    Tests for the courseware.render_xblock endpoint.
    This class overrides the get_response method, which is used by
    the tests defined in RenderXBlockTestMixin.
    """

    def setUp(self):
        reload_django_url_config()
        super(TestRenderXBlock, self).setUp()

    def get_response(self, url_encoded_params=None):
        """
        Overridable method to get the response from the endpoint that is being tested.
        """
        url = reverse('render_xblock', kwargs={"usage_key_string": unicode(self.html_block.location)})
        if url_encoded_params:
            url += '?' + url_encoded_params
        return self.client.get(url)


class TestRenderXBlockSelfPaced(TestRenderXBlock):
    """
    Test rendering XBlocks for a self-paced course. Relies on the query
    count assertions in the tests defined by RenderXBlockMixin.
    """

    def setUp(self):
        super(TestRenderXBlockSelfPaced, self).setUp()
        SelfPacedConfiguration(enabled=True).save()

    def course_options(self):
        return {'self_paced': True}
