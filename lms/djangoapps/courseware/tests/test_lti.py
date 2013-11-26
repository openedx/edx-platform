"""LTI integration tests"""

import oauthlib
from . import BaseTestXmodule
from collections import OrderedDict
import mock


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

        self.correct_headers = {
            u'user_id': unicode(self.item_descriptor.xmodule_runtime.anonymous_student_id),
            u'oauth_callback': u'about:blank',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',
            u'role': u'student',

            u'resource_link_id': u'i4x%3A//MITx/999/lti/lti_3',
            u'lis_outcome_service_url': 'http://edx.orgi4x://MITx/999/lti/lti_3/grade_handler',
            u'lis_result_sourcedid': u':i4x%253A//MITx/999/lti/lti_3:student',

            u'oauth_nonce': mocked_nonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
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
            'display_name': self.item_module.display_name,
            'input_fields': self.correct_headers,
            'element_class': self.item_module.category,
            'element_id': self.item_module.location.html_id(),
            'launch_url': 'http://www.example.com',  # default value
            'open_in_a_new_page': True,
        }

        self.assertEqual(
            generated_context,
            self.runtime.render_template('lti.html', expected_context),
        )
