"""LTI integration tests"""

import oauthlib
from . import BaseTestXmodule
from collections import OrderedDict
import mock

import courseware.grades as grades
from xmodule.modulestore.django import modulestore
from student.tests.factories import UserFactory
from django.test.client import RequestFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestLTI(BaseTestXmodule):
    """
    Integration test for lti xmodule.

    It checks overall code, by assuring that context that goes to template is correct.
    As part of that, checks oauth signature generation by mocking signing function
    of `oauthlib` library.
    """
    CATEGORY = "lti"
    grading_policy = None

    def set_up_course(self, **course_kwargs):
        """
        Create a stock coursecourse with a specific due date.

        :param course_kwargs: All kwargs are passed to through to the :class:`CourseFactory`
        """

        course = CourseFactory(**course_kwargs)
        chapter = ItemFactory(category='chapter', parent_location=course.location)  # pylint: disable=no-member
        section = self.section = ItemFactory(
            category='sequential',
            parent_location=chapter.location,
            metadata={'graded': True, 'format': 'Homework'}
        )
        vertical = ItemFactory(category='vertical', parent_location=section.location)
        ItemFactory(category=self.CATEGORY, parent_location=vertical.location)

        course = modulestore().get_instance(course.id, course.location)  # pylint: disable=no-member

        return course

    def setUp(self):
        """
        Mock oauth1 signing of requests library for testing.
        """
        super(TestLTI, self).setUp()
        mocked_nonce = u'135685044251684026041377608307'
        mocked_timestamp = u'1234567890'
        mocked_signature_after_sign = u'my_signature%3D'
        mocked_decoded_signature = u'my_signature='

        self.correct_headers = {
            u'oauth_callback': u'about:blank',
            u'lis_outcome_service_url': '',
            u'lis_result_sourcedid': '',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',

            u'oauth_nonce': mocked_nonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
            u'user_id': self.item_descriptor.xmodule_runtime.anonymous_student_id,
            u'role': u'student',
            u'oauth_signature': mocked_decoded_signature
        }

        saved_sign = oauthlib.oauth1.Client.sign

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
            headers[u'Authorization'] = ', '.join([k+'="'+v+'"' for k, v in old_parsed.items()])
            return None, headers, None

        patcher = mock.patch.object(oauthlib.oauth1.Client, "sign", mocked_sign)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_lti_constructor(self):
        """
        Makes sure that all parameters extracted.
        """
        generated_context = self.item_module.render('student_view').content
        expected_context = {
            'input_fields': self.correct_headers,
            'display_name': self.item_module.display_name,
            'element_class': self.item_module.location.category,
            'element_id': self.item_module.location.html_id(),
            'launch_url': 'http://www.example.com',  # default value
            'open_in_a_new_page': True,
        }
        self.assertEqual(
            generated_context,
            self.runtime.render_template('lti.html', expected_context),
        )

    @mock.patch('xmodule.lti_module.LTIModule.get_score')
    def test_lti_grading(self, get_score):
        """
        Makes sure that LTI is graded.
        """
        weight = 0.15
        grading_policy = {
            "GRADER": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "HW",
                    "weight": weight
                },
            ]
        }
        mocked_score = {'score': 0.7, 'total': 1}
        get_score.return_value = mocked_score

        course = self.set_up_course(grading_policy=grading_policy)
        request_factory = RequestFactory()
        user = UserFactory.create()
        request = request_factory.get("foo")
        request.user = user

        grade_summary = grades.grade(user, request, course)
        actual_score = grade_summary['grade_breakdown'][0]['percent']

        self.assertEqual(
            actual_score,
            mocked_score['score']*weight
        )



