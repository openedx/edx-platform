# -*- coding: utf-8 -*-
"""Tests for LTI Xmodule LTIv2.0 functional logic."""
import datetime
import textwrap

from django.utils.timezone import UTC
from mock import Mock
from xmodule.lti_module import LTIDescriptor
from xmodule.lti_2_util import LTIError

from . import LogicTest


class LTI20RESTResultServiceTest(LogicTest):
    """Logic tests for LTI module. LTI2.0 REST ResultService"""
    descriptor_class = LTIDescriptor

    def setUp(self):
        super(LTI20RESTResultServiceTest, self).setUp()
        self.environ = {'wsgi.url_scheme': 'http', 'REQUEST_METHOD': 'POST'}
        self.system.get_real_user = Mock()
        self.system.publish = Mock()
        self.system.rebind_noauth_module_to_user = Mock()
        self.user_id = self.xmodule.runtime.anonymous_student_id
        self.lti_id = self.xmodule.lti_id
        self.xmodule.due = None
        self.xmodule.graceperiod = None

    def test_sanitize_get_context(self):
        """Tests that the get_context function does basic sanitization"""
        # get_context, unfortunately, requires a lot of mocking machinery
        mocked_course = Mock(name='mocked_course', lti_passports=['lti_id:test_client:test_secret'])
        modulestore = Mock(name='modulestore')
        modulestore.get_course.return_value = mocked_course
        runtime = Mock(name='runtime', modulestore=modulestore)
        self.xmodule.descriptor.runtime = runtime
        self.xmodule.lti_id = "lti_id"

        test_cases = (  # (before sanitize, after sanitize)
            (u"plaintext", u"plaintext"),
            (u"a <script>alert(3)</script>", u"a &lt;script&gt;alert(3)&lt;/script&gt;"),  # encodes scripts
            (u"<b>bold 包</b>", u"<b>bold 包</b>"),  # unicode, and <b> tags pass through
        )
        for case in test_cases:
            self.xmodule.score_comment = case[0]
            self.assertEqual(
                case[1],
                self.xmodule.get_context()['comment']
            )

    def test_lti20_rest_bad_contenttype(self):
        """
        Input with bad content type
        """
        with self.assertRaisesRegexp(LTIError, "Content-Type must be"):
            request = Mock(headers={u'Content-Type': u'Non-existent'})
            self.xmodule.verify_lti_2_0_result_rest_headers(request)

    def test_lti20_rest_failed_oauth_body_verify(self):
        """
        Input with bad oauth body hash verification
        """
        err_msg = "OAuth body verification failed"
        self.xmodule.verify_oauth_body_sign = Mock(side_effect=LTIError(err_msg))
        with self.assertRaisesRegexp(LTIError, err_msg):
            request = Mock(headers={u'Content-Type': u'application/vnd.ims.lis.v2.result+json'})
            self.xmodule.verify_lti_2_0_result_rest_headers(request)

    def test_lti20_rest_good_headers(self):
        """
        Input with good oauth body hash verification
        """
        self.xmodule.verify_oauth_body_sign = Mock(return_value=True)

        request = Mock(headers={u'Content-Type': u'application/vnd.ims.lis.v2.result+json'})
        self.xmodule.verify_lti_2_0_result_rest_headers(request)
        #  We just want the above call to complete without exceptions, and to have called verify_oauth_body_sign
        self.assertTrue(self.xmodule.verify_oauth_body_sign.called)

    BAD_DISPATCH_INPUTS = [
        None,
        u"",
        u"abcd"
        u"notuser/abcd"
        u"user/"
        u"user//"
        u"user/gbere/"
        u"user/gbere/xsdf"
        u"user/ಠ益ಠ"  # not alphanumeric
    ]

    def test_lti20_rest_bad_dispatch(self):
        """
        Test the error cases for the "dispatch" argument to the LTI 2.0 handler.  Anything that doesn't
        fit the form user/<anon_id>
        """
        for einput in self.BAD_DISPATCH_INPUTS:
            with self.assertRaisesRegexp(LTIError, "No valid user id found in endpoint URL"):
                self.xmodule.parse_lti_2_0_handler_suffix(einput)

    GOOD_DISPATCH_INPUTS = [
        (u"user/abcd3", u"abcd3"),
        (u"user/Äbcdè2", u"Äbcdè2"),  # unicode, just to make sure
    ]

    def test_lti20_rest_good_dispatch(self):
        """
        Test the good cases for the "dispatch" argument to the LTI 2.0 handler.  Anything that does
        fit the form user/<anon_id>
        """
        for ginput, expected in self.GOOD_DISPATCH_INPUTS:
            self.assertEquals(self.xmodule.parse_lti_2_0_handler_suffix(ginput), expected)

    BAD_JSON_INPUTS = [
        # (bad inputs, error message expected)
        ([
            u"kk",   # ValueError
            u"{{}",  # ValueError
            u"{}}",  # ValueError
            3,       # TypeError
            {},      # TypeError
        ], u"Supplied JSON string in request body could not be decoded"),
        ([
            u"3",        # valid json, not array or object
            u"[]",       # valid json, array too small
            u"[3, {}]",  # valid json, 1st element not an object
        ], u"Supplied JSON string is a list that does not contain an object as the first element"),
        ([
            u'{"@type": "NOTResult"}',  # @type key must have value 'Result'
        ], u"JSON object does not contain correct @type attribute"),
        ([
            # @context missing
            u'{"@type": "Result", "resultScore": 0.1}',
        ], u"JSON object does not contain required key"),
        ([
            u'''
            {"@type": "Result",
             "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
             "resultScore": 100}'''  # score out of range
        ], u"score value outside the permitted range of 0-1."),
        ([
            u'''
            {"@type": "Result",
             "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
             "resultScore": "1b"}''',   # score ValueError
            u'''
            {"@type": "Result",
             "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
             "resultScore": {}}''',   # score TypeError
        ], u"Could not convert resultScore to float"),
    ]

    def test_lti20_bad_json(self):
        """
        Test that bad json_str to parse_lti_2_0_result_json inputs raise appropriate LTI Error
        """
        for error_inputs, error_message in self.BAD_JSON_INPUTS:
            for einput in error_inputs:
                with self.assertRaisesRegexp(LTIError, error_message):
                    self.xmodule.parse_lti_2_0_result_json(einput)

    GOOD_JSON_INPUTS = [
        (u'''
        {"@type": "Result",
         "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
         "resultScore": 0.1}''', u""),  # no comment means we expect ""
        (u'''
        [{"@type": "Result",
         "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
         "@id": "anon_id:abcdef0123456789",
         "resultScore": 0.1}]''', u""),  # OK to have array of objects -- just take the first.  @id is okay too
        (u'''
        {"@type": "Result",
         "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
         "resultScore": 0.1,
         "comment": "ಠ益ಠ"}''', u"ಠ益ಠ"),  # unicode comment
    ]

    def test_lti20_good_json(self):
        """
        Test the parsing of good comments
        """
        for json_str, expected_comment in self.GOOD_JSON_INPUTS:
            score, comment = self.xmodule.parse_lti_2_0_result_json(json_str)
            self.assertEqual(score, 0.1)
            self.assertEqual(comment, expected_comment)

    GOOD_JSON_PUT = textwrap.dedent(u"""
        {"@type": "Result",
         "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
         "@id": "anon_id:abcdef0123456789",
         "resultScore": 0.1,
         "comment": "ಠ益ಠ"}
    """).encode('utf-8')

    GOOD_JSON_PUT_LIKE_DELETE = textwrap.dedent(u"""
        {"@type": "Result",
         "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
         "@id": "anon_id:abcdef0123456789",
         "comment": "ಠ益ಠ"}
    """).encode('utf-8')

    def get_signed_lti20_mock_request(self, body, method=u'PUT'):
        """
        Example of signed from LTI 2.0 Provider.  Signatures and hashes are example only and won't verify
        """
        mock_request = Mock()
        mock_request.headers = {
            'Content-Type': 'application/vnd.ims.lis.v2.result+json',
            'Authorization': (
                u'OAuth oauth_nonce="135685044251684026041377608307", '
                u'oauth_timestamp="1234567890", oauth_version="1.0", '
                u'oauth_signature_method="HMAC-SHA1", '
                u'oauth_consumer_key="test_client_key", '
                u'oauth_signature="my_signature%3D", '
                u'oauth_body_hash="gz+PeJZuF2//n9hNUnDj2v5kN70="'
            )
        }
        mock_request.url = u'http://testurl'
        mock_request.http_method = method
        mock_request.method = method
        mock_request.body = body
        return mock_request

    USER_STANDIN = Mock()
    USER_STANDIN.id = 999

    def setup_system_xmodule_mocks_for_lti20_request_test(self):
        """
        Helper fn to set up mocking for lti 2.0 request test
        """
        self.system.get_real_user = Mock(return_value=self.USER_STANDIN)
        self.xmodule.max_score = Mock(return_value=1.0)
        self.xmodule.get_client_key_secret = Mock(return_value=('test_client_key', u'test_client_secret'))
        self.xmodule.verify_oauth_body_sign = Mock()

    def test_lti20_put_like_delete_success(self):
        """
        The happy path for LTI 2.0 PUT that acts like a delete
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        SCORE = 0.55  # pylint: disable=invalid-name
        COMMENT = u"ಠ益ಠ"  # pylint: disable=invalid-name
        self.xmodule.module_score = SCORE
        self.xmodule.score_comment = COMMENT
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT_LIKE_DELETE)
        # Now call the handler
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        # Now assert there's no score
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.xmodule.module_score)
        self.assertEqual(self.xmodule.score_comment, u"")
        (_, evt_type, called_grade_obj), _ = self.system.publish.call_args
        self.assertEqual(called_grade_obj, {'user_id': self.USER_STANDIN.id, 'value': None, 'max_value': None})
        self.assertEqual(evt_type, 'grade')

    def test_lti20_delete_success(self):
        """
        The happy path for LTI 2.0 DELETE
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        SCORE = 0.55  # pylint: disable=invalid-name
        COMMENT = u"ಠ益ಠ"  # pylint: disable=invalid-name
        self.xmodule.module_score = SCORE
        self.xmodule.score_comment = COMMENT
        mock_request = self.get_signed_lti20_mock_request("", method=u'DELETE')
        # Now call the handler
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        # Now assert there's no score
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.xmodule.module_score)
        self.assertEqual(self.xmodule.score_comment, u"")
        (_, evt_type, called_grade_obj), _ = self.system.publish.call_args
        self.assertEqual(called_grade_obj, {'user_id': self.USER_STANDIN.id, 'value': None, 'max_value': None})
        self.assertEqual(evt_type, 'grade')

    def test_lti20_put_set_score_success(self):
        """
        The happy path for LTI 2.0 PUT that sets a score
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        # Now call the handler
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        # Now assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.xmodule.module_score, 0.1)
        self.assertEqual(self.xmodule.score_comment, u"ಠ益ಠ")
        (_, evt_type, called_grade_obj), _ = self.system.publish.call_args
        self.assertEqual(evt_type, 'grade')
        self.assertEqual(called_grade_obj, {'user_id': self.USER_STANDIN.id, 'value': 0.1, 'max_value': 1.0})

    def test_lti20_get_no_score_success(self):
        """
        The happy path for LTI 2.0 GET when there's no score
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        mock_request = self.get_signed_lti20_mock_request("", method=u'GET')
        # Now call the handler
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        # Now assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
                                         "@type": "Result"})

    def test_lti20_get_with_score_success(self):
        """
        The happy path for LTI 2.0 GET when there is a score
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        SCORE = 0.55  # pylint: disable=invalid-name
        COMMENT = u"ಠ益ಠ"  # pylint: disable=invalid-name
        self.xmodule.module_score = SCORE
        self.xmodule.score_comment = COMMENT
        mock_request = self.get_signed_lti20_mock_request("", method=u'GET')
        # Now call the handler
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        # Now assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
                                         "@type": "Result",
                                         "resultScore": SCORE,
                                         "comment": COMMENT})

    UNSUPPORTED_HTTP_METHODS = ["OPTIONS", "HEAD", "POST", "TRACE", "CONNECT"]

    def test_lti20_unsupported_method_error(self):
        """
        Test we get a 404 when we don't GET or PUT
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        for bad_method in self.UNSUPPORTED_HTTP_METHODS:
            mock_request.method = bad_method
            response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
            self.assertEqual(response.status_code, 404)

    def test_lti20_request_handler_bad_headers(self):
        """
        Test that we get a 401 when header verification fails
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        self.xmodule.verify_lti_2_0_result_rest_headers = Mock(side_effect=LTIError())
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        self.assertEqual(response.status_code, 401)

    def test_lti20_request_handler_bad_dispatch_user(self):
        """
        Test that we get a 404 when there's no (or badly formatted) user specified in the url
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, None)
        self.assertEqual(response.status_code, 404)

    def test_lti20_request_handler_bad_json(self):
        """
        Test that we get a 404 when json verification fails
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        self.xmodule.parse_lti_2_0_result_json = Mock(side_effect=LTIError())
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        self.assertEqual(response.status_code, 404)

    def test_lti20_request_handler_bad_user(self):
        """
        Test that we get a 404 when the supplied user does not exist
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        self.system.get_real_user = Mock(return_value=None)
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        self.assertEqual(response.status_code, 404)

    def test_lti20_request_handler_grade_past_due(self):
        """
        Test that we get a 404 when accept_grades_past_due is False and it is past due
        """
        self.setup_system_xmodule_mocks_for_lti20_request_test()
        self.xmodule.due = datetime.datetime.now(UTC())
        self.xmodule.accept_grades_past_due = False
        mock_request = self.get_signed_lti20_mock_request(self.GOOD_JSON_PUT)
        response = self.xmodule.lti_2_0_result_rest_handler(mock_request, "user/abcd")
        self.assertEqual(response.status_code, 404)
