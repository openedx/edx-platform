"""
Tests for the findusers script.
"""
import datetime
import mock
import pytz
import StringIO
import unittest


from linkedin.management.commands import findusers


class FindUsersTests(unittest.TestCase):
    """
    Tests for the findusers script.
    """

    @mock.patch('linkedin.management.commands.findusers.timezone')
    def test_get_call_limits_in_safe_harbor(self, timezone):
        """
        We should be able to perform unlimited API calls during "safe harbor".
        """
        fut = findusers.get_call_limits
        tzinfo = pytz.timezone('US/Eastern')
        timezone.now.return_value = datetime.datetime(
            2013, 12, 14, 0, 0, tzinfo=tzinfo)
        self.assertEqual(fut(), (-1, 80, 1))
        timezone.now.return_value = datetime.datetime(
            2013, 12, 13, 21, 1, tzinfo=tzinfo)
        self.assertEqual(fut(), (-1, 80, 1))
        timezone.now.return_value = datetime.datetime(
            2013, 12, 15, 7, 59, tzinfo=tzinfo)
        self.assertEqual(fut(), (-1, 80, 1))

    @mock.patch('linkedin.management.commands.findusers.timezone')
    def test_get_call_limits_in_business_hours(self, timezone):
        """
        During business hours we shouldn't be able to make any API calls.
        """
        fut = findusers.get_call_limits
        tzinfo = pytz.timezone('US/Eastern')
        timezone.now.return_value = datetime.datetime(
            2013, 12, 11, 11, 3, tzinfo=tzinfo)
        self.assertEqual(fut(), (0, 0, 0))
        timezone.now.return_value = datetime.datetime(
            2013, 12, 13, 20, 59, tzinfo=tzinfo)
        self.assertEqual(fut(), (0, 0, 0))
        timezone.now.return_value = datetime.datetime(
            2013, 12, 16, 8, 1, tzinfo=tzinfo)
        self.assertEqual(fut(), (0, 0, 0))

    @mock.patch('linkedin.management.commands.findusers.timezone')
    def test_get_call_limits_on_weeknights(self, timezone):
        """
        On weeknights outside of "safe harbor" we can only make limited API
        calls.
        """
        fut = findusers.get_call_limits
        tzinfo = pytz.timezone('US/Eastern')
        timezone.now.return_value = datetime.datetime(
            2013, 12, 11, 21, 3, tzinfo=tzinfo)
        self.assertEqual(fut(), (500, 80, 1))
        timezone.now.return_value = datetime.datetime(
            2013, 12, 11, 7, 59, tzinfo=tzinfo)
        self.assertEqual(fut(), (500, 80, 1))

    @mock.patch('linkedin.management.commands.findusers.time')
    @mock.patch('linkedin.management.commands.findusers.User')
    @mock.patch('linkedin.management.commands.findusers.LinkedinAPI')
    @mock.patch('linkedin.management.commands.findusers.get_call_limits')
    def test_command_success_recheck_no_limits(self, get_call_limits, apicls,
                                               usercls, time):
        """
        Test rechecking all users with no API limits.
        """
        fut = findusers.Command().handle
        get_call_limits.return_value = (-1, 6, 42)
        api = apicls.return_value
        users = [mock.Mock(email=i) for i in xrange(10)]
        usercls.objects.all.return_value = users

        def dummy_batch(emails):
            "Mock LinkedIn API."
            return [email % 2 == 0 for email in emails]
        api.batch = dummy_batch
        fut(recheck=True)
        time.sleep.assert_called_once_with(42)
        self.assertEqual([u.linkedin.has_linkedin_account for u in users],
                         [i % 2 == 0 for i in xrange(10)])

    @mock.patch('linkedin.management.commands.findusers.time')
    @mock.patch('linkedin.management.commands.findusers.User')
    @mock.patch('linkedin.management.commands.findusers.LinkedinAPI')
    @mock.patch('linkedin.management.commands.findusers.get_call_limits')
    def test_command_success_no_recheck_no_limits(self, get_call_limits, apicls,
                                                  usercls, time):
        """
        Test checking only unchecked users, with no API limits.
        """
        fut = findusers.Command().handle
        get_call_limits.return_value = (-1, 6, 42)
        api = apicls.return_value
        users = [mock.Mock(email=i) for i in xrange(10)]
        for user in users[:6]:
            user.linkedin.has_linkedin_account = user.email % 2 == 0
        for user in users[6:]:
            user.linkedin.has_linkedin_account = None
        usercls.objects.all.return_value = users

        def dummy_batch(emails):
            "Mock LinkedIn API."
            self.assertEqual(len(emails), 4)
            return [email % 2 == 0 for email in emails]
        api.batch = dummy_batch
        fut()
        time.sleep.assert_not_called()
        self.assertEqual([u.linkedin.has_linkedin_account for u in users],
                         [i % 2 == 0 for i in xrange(10)])

    @mock.patch('linkedin.management.commands.findusers.time')
    @mock.patch('linkedin.management.commands.findusers.User')
    @mock.patch('linkedin.management.commands.findusers.LinkedinAPI')
    @mock.patch('linkedin.management.commands.findusers.get_call_limits')
    def test_command_success_no_recheck_no_users(self, get_call_limits, apicls,
                                                 usercls, time):
        """
        Test no users to check.
        """
        fut = findusers.Command().handle
        get_call_limits.return_value = (-1, 6, 42)
        api = apicls.return_value
        users = [mock.Mock(email=i) for i in xrange(10)]
        for user in users:
            user.linkedin.has_linkedin_account = user.email % 2 == 0
        usercls.objects.all.return_value = users

        def dummy_batch(_):
            "Mock LinkedIn API."
            self.assertTrue(False)  # shouldn't be called
        api.batch = dummy_batch
        fut()
        time.sleep.assert_not_called()
        self.assertEqual([u.linkedin.has_linkedin_account for u in users],
                         [i % 2 == 0 for i in xrange(10)])

    @mock.patch('linkedin.management.commands.findusers.time')
    @mock.patch('linkedin.management.commands.findusers.User')
    @mock.patch('linkedin.management.commands.findusers.LinkedinAPI')
    @mock.patch('linkedin.management.commands.findusers.get_call_limits')
    def test_command_success_recheck_with_limit(self, get_call_limits, apicls,
                                                usercls, time):
        """
        Test recheck all users with API limit.
        """
        command = findusers.Command()
        command.stderr = StringIO.StringIO()
        fut = command.handle
        get_call_limits.return_value = (9, 6, 42)
        api = apicls.return_value
        users = [mock.Mock(email=i) for i in xrange(10)]
        for user in users:
            user.linkedin.has_linkedin_account = None
        usercls.objects.all.return_value = users

        def dummy_batch(emails):
            "Mock LinkedIn API."
            return [email % 2 == 0 for email in emails]
        api.batch = dummy_batch
        fut()
        time.sleep.assert_called_once_with(42)
        self.assertEqual([u.linkedin.has_linkedin_account for u in users[:9]],
                         [i % 2 == 0 for i in xrange(9)])
        self.assertEqual(users[9].linkedin.has_linkedin_account, None)
        self.assertTrue(command.stderr.getvalue().startswith("WARNING"))
