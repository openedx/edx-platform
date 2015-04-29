"""LTI integration tests"""

from collections import OrderedDict
import json
import mock
from nose.plugins.attrib import attr
import oauthlib
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.tests import BaseTestXmodule
from courseware.views import get_course_lti_endpoints
from lms.djangoapps.lms_xblock.runtime import quote_slashes
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.x_module import STUDENT_VIEW


@attr('shard_1')
class TestLTI(BaseTestXmodule):
    """
    Integration test for lti xmodule.

    It checks overall code, by assuring that context that goes to template is correct.
    As part of that, checks oauth signature generation by mocking signing function
    of `oauthlib` library.
    """
    CATEGORY = "lti"

    def setUp(self):
        """
        Mock oauth1 signing of requests library for testing.
        """
        super(TestLTI, self).setUp()
        mocked_nonce = u'135685044251684026041377608307'
        mocked_timestamp = u'1234567890'
        mocked_signature_after_sign = u'my_signature%3D'
        mocked_decoded_signature = u'my_signature='

        # Note: this course_id is actually a course_key
        context_id = self.item_descriptor.course_id.to_deprecated_string()
        user_id = unicode(self.item_descriptor.xmodule_runtime.anonymous_student_id)
        hostname = self.item_descriptor.xmodule_runtime.hostname
        resource_link_id = unicode(urllib.quote('{}-{}'.format(hostname, self.item_descriptor.location.html_id())))

        sourcedId = "{context}:{resource_link}:{user_id}".format(
            context=urllib.quote(context_id),
            resource_link=resource_link_id,
            user_id=user_id
        )

        self.correct_headers = {
            u'user_id': user_id,
            u'oauth_callback': u'about:blank',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',
            u'roles': u'Student',
            u'context_id': context_id,

            u'resource_link_id': resource_link_id,
            u'lis_result_sourcedid': sourcedId,

            u'oauth_nonce': mocked_nonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
            u'oauth_signature': mocked_decoded_signature
        }

        saved_sign = oauthlib.oauth1.Client.sign

        self.expected_context = {
            'display_name': self.item_descriptor.display_name,
            'input_fields': self.correct_headers,
            'element_class': self.item_descriptor.category,
            'element_id': self.item_descriptor.location.html_id(),
            'launch_url': 'http://www.example.com',  # default value
            'open_in_a_new_page': True,
            'form_url': self.item_descriptor.xmodule_runtime.handler_url(self.item_descriptor,
                                                                         'preview_handler').rstrip('/?'),
            'hide_launch': False,
            'has_score': False,
            'module_score': None,
            'comment': u'',
            'weight': 1.0,
            'ask_to_send_username': self.item_descriptor.ask_to_send_username,
            'ask_to_send_email': self.item_descriptor.ask_to_send_email,
            'description': self.item_descriptor.description,
            'button_text': self.item_descriptor.button_text,
            'accept_grades_past_due': self.item_descriptor.accept_grades_past_due,
        }

        def mocked_sign(self, *args, **kwargs):
            """
            Mocked oauth1 sign function.
            """
            # self is <oauthlib.oauth1.rfc5849.Client object> here:
            __, headers, __ = saved_sign(self, *args, **kwargs)
            # we should replace nonce, timestamp and signed_signature in headers:
            old = headers[u'Authorization']
            old_parsed = OrderedDict([param.strip().replace('"', '').split('=') for param in old.split(',')])
            old_parsed[u'OAuth oauth_nonce'] = mocked_nonce
            old_parsed[u'oauth_timestamp'] = mocked_timestamp
            old_parsed[u'oauth_signature'] = mocked_signature_after_sign
            headers[u'Authorization'] = ', '.join([k + '="' + v + '"' for k, v in old_parsed.items()])
            return None, headers, None

        patcher = mock.patch.object(oauthlib.oauth1.Client, "sign", mocked_sign)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_lti_constructor(self):
        generated_content = self.item_descriptor.render(STUDENT_VIEW).content
        expected_content = self.runtime.render_template('lti.html', self.expected_context)
        self.assertEqual(generated_content, expected_content)

    def test_lti_preview_handler(self):
        generated_content = self.item_descriptor.preview_handler(None, None).body
        expected_content = self.runtime.render_template('lti_form.html', self.expected_context)
        self.assertEqual(generated_content, expected_content)


@attr('shard_1')
class TestLTIModuleListing(ModuleStoreTestCase):
    """
    a test for the rest endpoint that lists LTI modules in a course
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"

    def setUp(self):
        """Create course, 2 chapters, 2 sections"""
        super(TestLTIModuleListing, self).setUp()
        self.course = CourseFactory.create(display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.chapter1 = ItemFactory.create(
            parent_location=self.course.location,
            display_name="chapter1",
            category='chapter')
        self.section1 = ItemFactory.create(
            parent_location=self.chapter1.location,
            display_name="section1",
            category='sequential')
        self.chapter2 = ItemFactory.create(
            parent_location=self.course.location,
            display_name="chapter2",
            category='chapter')
        self.section2 = ItemFactory.create(
            parent_location=self.chapter2.location,
            display_name="section2",
            category='sequential')

        # creates one draft and one published lti module, in different sections
        self.lti_published = ItemFactory.create(
            parent_location=self.section1.location,
            display_name="lti published",
            category="lti",
            location=self.course.id.make_usage_key('lti', 'lti_published'),
        )
        self.lti_draft = ItemFactory.create(
            parent_location=self.section2.location,
            display_name="lti draft",
            category="lti",
            location=self.course.id.make_usage_key('lti', 'lti_draft'),
            publish_item=False,
        )

    def expected_handler_url(self, handler):
        """convenience method to get the reversed handler urls"""
        return "https://{}{}".format(settings.SITE_NAME, reverse(
            'courseware.module_render.handle_xblock_callback_noauth',
            args=[
                self.course.id.to_deprecated_string(),
                quote_slashes(unicode(self.lti_published.scope_ids.usage_id.to_deprecated_string()).encode('utf-8')),
                handler
            ]
        ))

    def test_lti_rest_bad_course(self):
        """Tests what happens when the lti listing rest endpoint gets a bad course_id"""
        bad_ids = [u"sf", u"dne/dne/dne", u"fo/ey/\\u5305"]
        for bad_course_id in bad_ids:
            lti_rest_endpoints_url = 'courses/{}/lti_rest_endpoints/'.format(bad_course_id)
            response = self.client.get(lti_rest_endpoints_url)
            self.assertEqual(404, response.status_code)

    def test_lti_rest_listing(self):
        """tests that the draft lti module is part of the endpoint response"""
        request = mock.Mock()
        request.method = 'GET'
        response = get_course_lti_endpoints(request, course_id=self.course.id.to_deprecated_string())

        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['Content-Type'])

        expected = {
            "lti_1_1_result_service_xml_endpoint": self.expected_handler_url('grade_handler'),
            "lti_2_0_result_service_json_endpoint":
            self.expected_handler_url('lti_2_0_result_rest_handler') + "/user/{anon_user_id}",
            "display_name": self.lti_published.display_name,
        }
        self.assertEqual([expected], json.loads(response.content))

    def test_lti_rest_non_get(self):
        """tests that the endpoint returns 404 when hit with NON-get"""
        DISALLOWED_METHODS = ("POST", "PUT", "DELETE", "HEAD", "OPTIONS")  # pylint: disable=invalid-name
        for method in DISALLOWED_METHODS:
            request = mock.Mock()
            request.method = method
            response = get_course_lti_endpoints(request, self.course.id.to_deprecated_string())
            self.assertEqual(405, response.status_code)
