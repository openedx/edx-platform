import mock
import StringIO

from django.core.management.base import CommandError
from django.test import TestCase

from linkedin.management.commands import LinkedinAPI
from linkedin.models import LinkedInToken


class LinkedinAPITests(TestCase):

    def setUp(self):
        patcher = mock.patch('linkedin.management.commands.uuid.uuid4')
        uuid4 = patcher.start()
        uuid4.return_value = '0000-0000'
        self.addCleanup(patcher.stop)

    def make_one(self):
        return LinkedinAPI(DummyCommand())

    @mock.patch('django.conf.settings.LINKEDIN_API', None)
    def test_ctor_no_api_config(self):
        with self.assertRaises(CommandError):
            self.make_one()

    def test_ctor_no_token(self):
        api = self.make_one()
        self.assertEqual(api.token, None)

    def test_ctor_with_token(self):
        token = LinkedInToken()
        token.save()
        api = self.make_one()
        self.assertEqual(api.token, token)

    def test_http_error(self):
        api = self.make_one()
        with self.assertRaises(CommandError):
            api.http_error(DummyHTTPError(), "That didn't work")
        self.assertEqual(
            api.command.stderr.getvalue(),
            "!!ERROR!!"
            "HTTPError OMG!"
            "OMG OHNOES!")

    def test_authorization_url(self):
        api = self.make_one()
        self.assertEqual(
            api.authorization_url(),
            'https://www.linkedin.com/uas/oauth2/authorization?'
            'response_type=code&client_id=12345&state=0000-0000&'
            'redirect_uri=http://bar.foo')

    def test_get_authorization_code(self):
        fut = self.make_one().get_authorization_code
        self.assertEqual(
            fut('http://foo.bar/?state=0000-0000&code=54321'), '54321')

    def test_access_token_url(self):
        fut = self.make_one().access_token_url
        self.assertEqual(
            fut('54321'),
            'https://www.linkedin.com/uas/oauth2/accessToken?'
            'grant_type=authorization_code&code=54321&'
            'redirect_uri=http://bar.foo&client_id=12345&client_secret=SECRET')

    def test_get_access_token(self):
        api = self.make_one()
        api.call_json_api = mock.Mock(return_value={'access_token': '777'})
        self.assertEqual(api.get_access_token('54321'), '777')
        token = LinkedInToken.objects.get()
        self.assertEqual(token.access_token, '777')

    def test_get_access_token_overwrite_previous(self):
        LinkedInToken(access_token='888').save()
        api = self.make_one()
        api.call_json_api = mock.Mock(return_value={'access_token': '777'})
        self.assertEqual(api.get_access_token('54321'), '777')
        token = LinkedInToken.objects.get()
        self.assertEqual(token.access_token, '777')

    def test_require_token_no_token(self):
        fut = self.make_one().require_token
        with self.assertRaises(CommandError):
            fut()

    def test_require_token(self):
        LinkedInToken().save()
        fut = self.make_one().require_token
        fut()

    def test_batch_url(self):
        LinkedInToken(access_token='777').save()
        fut = self.make_one().batch_url
        emails = ['foo@bar', 'bar@foo']
        self.assertEquals(
            fut(emails),
            'https://api.linkedin.com/v1/people::(email=foo@bar,email=bar@foo):'
            '(id)?oauth2_access_token=777')

    def test_batch(self):
        LinkedInToken(access_token='777').save()
        api = self.make_one()
        api.call_json_api = mock.Mock(return_value={
            'values': [{'_key': 'email=bar@foo'}]})
        emails = ['foo@bar', 'bar@foo']
        self.assertEqual(list(api.batch(emails)), [False, True])


class DummyCommand(object):

    def __init__(self):
        self.stderr = StringIO.StringIO()


class DummyHTTPError(object):

    def __str__(self):
        return 'HTTPError OMG!'

    def read(self):
        return 'OMG OHNOES!'
