from django.test import TestCase
from django.core.management.base import CommandError
from mock import patch
from pgreport.management.commands import progress_report as pr
from xmodule.exceptions import NotFoundError


class ProgressReportCommandTestCase(TestCase):
    """For unit test."""

    def setUp(self):
        self.args = ["org/num/run"]
        self.options_get = {'create': False, 'delete': False}
        self.options_create = {'create': True, 'delete': False}
        self.options_delete = {'create': False, 'delete': True}
        self.options_error = {'create': True, 'delete': True}

    def tearDown(self):
        pass

    @patch('pgreport.management.commands.progress_report.call_command')
    @patch('pgreport.management.commands.progress_report.check_course_id')
    @patch('pgreport.management.commands.progress_report.delete_pgreport_csv')
    @patch('pgreport.management.commands.progress_report.get_pgreport_csv')
    def test_handle(self, get_mock, del_mock, check_mock, call_mock):
        pr.Command().handle(*self.args, **self.options_get)
        get_mock.assert_called_once_with(*self.args)

        pr.Command().handle(*self.args, **self.options_create)
        call_mock.assert_called_once_with(
            'create_report_task', *['create'], **{'course_id': self.args[0]})

        pr.Command().handle(*self.args, **self.options_delete)
        del_mock.assert_called_once_with(*self.args)

        msg = '^"course_id" is not specified$'
        with self.assertRaisesRegexp(CommandError, msg):
            pr.Command().handle(*[], **self.options_get)

        msg = '^Cannot specify "-c" option and "-d" option at the same time.$'
        with self.assertRaisesRegexp(CommandError, msg):
            pr.Command().handle(*self.args, **self.options_error)

        msg = '^CSV not found.$'
        with self.assertRaisesRegexp(CommandError, msg):
            get_mock.side_effect = NotFoundError()
            pr.Command().handle(*self.args, **self.options_get)
