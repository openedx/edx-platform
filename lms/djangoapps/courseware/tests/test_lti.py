"""LTI test"""

import requests
from . import BaseTestXmodule


class TestLTI(BaseTestXmodule):
    """Integration test for word cloud xmodule."""
    CATEGORY = "lti"

    def setUp(self):
        super(TestLTI, self).setUp()
        mocked_noonce = u'135685044251684026041377608307'
        mocked_timestamp = u'1234567890'
        mocked_signed_signature = u'my_signature%3D'
        mocked_decoded_signature = u'my_signature='

        self.correct_headers = {
            u'oauth_nonce': mocked_noonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
            u'oauth_signature': mocked_decoded_signature}

        saved_sign = requests.auth.Client.sign

        def mocked_sign(self, *args, **kwargs):
            """Mocked oauth1 sign function"""
            # self is <oauthlib.oauth1.rfc5849.Client object at 0x107456e90> here:
            _, headers, _ = saved_sign(self, *args, **kwargs)
            # we should replace noonce, timestamp and signed_signature in headers:
            old = headers[u'Authorization']
            new = old[:19] + mocked_noonce + old[49:69] + mocked_timestamp + \
                old[79:179] + mocked_signed_signature + old[-1]
            headers[u'Authorization'] = new
            return None, headers, None

        requests.auth.Client.sign = mocked_sign

    def test_lti_constructor(self):
        """Make sure that all parameters extracted """
        fragment = self.runtime.render(self.item_module, None, 'student_view')
        expected_context = {
            'element_class': self.item_module.location.category,
            'element_id': self.item_module.location.html_id(),
            'lti_url': '',  # default value
        }
        self.correct_headers.update(expected_context)
        # import ipdb; ipdb.set_trace()
        self.assertEqual(
            fragment.content,
            self.runtime.render_template('lti.html', self.correct_headers)
        )
