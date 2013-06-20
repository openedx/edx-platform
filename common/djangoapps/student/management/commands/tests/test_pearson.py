'''
Created on Jan 17, 2013

@author: brian
'''
import logging
import os
from tempfile import mkdtemp
import cStringIO
import shutil
import sys

from django.test import TestCase
from django.core.management import call_command
from nose.plugins.skip import SkipTest

from student.models import User, TestCenterUser, get_testcenter_registration

log = logging.getLogger(__name__)


def create_tc_user(username):
    user = User.objects.create_user(username, '{}@edx.org'.format(username), 'fakepass')
    options = {
                   'first_name': 'TestFirst',
                   'last_name': 'TestLast',
                   'address_1': 'Test Address',
                   'city': 'TestCity',
                   'state': 'Alberta',
                   'postal_code': 'A0B 1C2',
                   'country': 'CAN',
                   'phone': '252-1866',
                   'phone_country_code': '1',
                    }
    call_command('pearson_make_tc_user', username, **options)
    return TestCenterUser.objects.get(user=user)


def create_tc_registration(username, course_id='org1/course1/term1', exam_code='exam1', accommodation_code=None):

    options = {'exam_series_code': exam_code,
               'eligibility_appointment_date_first': '2013-01-01T00:00',
               'eligibility_appointment_date_last': '2013-12-31T23:59',
               'accommodation_code': accommodation_code,
               'create_dummy_exam': True,
               }

    call_command('pearson_make_tc_registration', username, course_id, **options)
    user = User.objects.get(username=username)
    registrations = get_testcenter_registration(user, course_id, exam_code)
    return registrations[0]


def create_multiple_registrations(prefix='test'):
    username1 = '{}_multiple1'.format(prefix)
    create_tc_user(username1)
    create_tc_registration(username1)
    create_tc_registration(username1, course_id='org1/course2/term1')
    create_tc_registration(username1, exam_code='exam2')
    username2 = '{}_multiple2'.format(prefix)
    create_tc_user(username2)
    create_tc_registration(username2)
    username3 = '{}_multiple3'.format(prefix)
    create_tc_user(username3)
    create_tc_registration(username3, course_id='org1/course2/term1')
    username4 = '{}_multiple4'.format(prefix)
    create_tc_user(username4)
    create_tc_registration(username4, exam_code='exam2')


def get_command_error_text(*args, **options):
    stderr_string = None
    old_stderr = sys.stderr
    sys.stderr = cStringIO.StringIO()
    try:
        call_command(*args, **options)
    except SystemExit, why1:
        # The goal here is to catch CommandError calls.
        # But these are actually translated into nice messages,
        # and sys.exit(1) is then called.  For testing, we
        # want to catch what sys.exit throws, and get the
        # relevant text either from stdout or stderr.
        if (why1.message > 0):
            stderr_string = sys.stderr.getvalue()
        else:
            raise why1
    except Exception, why:
        raise why

    finally:
        sys.stderr = old_stderr

    if stderr_string is None:
        raise Exception("Expected call to {} to fail, but it succeeded!".format(args[0]))
    return stderr_string


def get_error_string_for_management_call(*args, **options):
    stdout_string = None
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = cStringIO.StringIO()
    sys.stderr = cStringIO.StringIO()
    try:
        call_command(*args, **options)
    except SystemExit, why1:
        # The goal here is to catch CommandError calls.
        # But these are actually translated into nice messages,
        # and sys.exit(1) is then called.  For testing, we
        # want to catch what sys.exit throws, and get the
        # relevant text either from stdout or stderr.
        if (why1.message == 1):
            stdout_string = sys.stdout.getvalue()
            stderr_string = sys.stderr.getvalue()
        else:
            raise why1
    except Exception, why:
        raise why

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    if stdout_string is None:
        raise Exception("Expected call to {} to fail, but it succeeded!".format(args[0]))
    return stdout_string, stderr_string


def get_file_info(dirpath):
    filelist = os.listdir(dirpath)
    print 'Files found: {}'.format(filelist)
    numfiles = len(filelist)
    if numfiles == 1:
        filepath = os.path.join(dirpath, filelist[0])
        with open(filepath, 'r') as cddfile:
            filecontents = cddfile.readlines()
            numlines = len(filecontents)
            return filepath, numlines
    else:
        raise Exception("Expected to find a single file in {}, but found {}".format(dirpath, filelist))


class PearsonTestCase(TestCase):
    '''
    Base class for tests running Pearson-related commands
    '''

    def assertErrorContains(self, error_message, expected):
        self.assertTrue(error_message.find(expected) >= 0, 'error message "{}" did not contain "{}"'.format(error_message, expected))

    def setUp(self):
        self.import_dir = mkdtemp(prefix="import")
        self.addCleanup(shutil.rmtree, self.import_dir)
        self.export_dir = mkdtemp(prefix="export")
        self.addCleanup(shutil.rmtree, self.export_dir)

    def tearDown(self):
        pass
        # and clean up the database:
#        TestCenterUser.objects.all().delete()
#        TestCenterRegistration.objects.all().delete()


class PearsonCommandTestCase(PearsonTestCase):

    def test_missing_demographic_fields(self):
        # We won't bother to test all details of form validation here.
        # It is enough to show that it works here, but deal with test cases for the form
        # validation in the student tests, not these management tests.
        username = 'baduser'
        User.objects.create_user(username, '{}@edx.org'.format(username), 'fakepass')
        options = {}
        error_string = get_command_error_text('pearson_make_tc_user', username, **options)
        self.assertTrue(error_string.find('Field Form errors encountered:') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  city') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  first_name') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  last_name') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  country') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  phone_country_code') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  phone') >= 0)
        self.assertTrue(error_string.find('Field Form Error:  address_1') >= 0)
        self.assertErrorContains(error_string, 'Field Form Error:  address_1')

    def test_create_good_testcenter_user(self):
        testcenter_user = create_tc_user("test_good_user")
        self.assertIsNotNone(testcenter_user)

    def test_create_good_testcenter_registration(self):
        username = 'test_good_registration'
        create_tc_user(username)
        registration = create_tc_registration(username)
        self.assertIsNotNone(registration)

    def test_cdd_missing_option(self):
        error_string = get_command_error_text('pearson_export_cdd', **{})
        self.assertErrorContains(error_string, 'Error: --destination or --dest-from-settings must be used')

    def test_ead_missing_option(self):
        error_string = get_command_error_text('pearson_export_ead', **{})
        self.assertErrorContains(error_string, 'Error: --destination or --dest-from-settings must be used')

    def test_export_single_cdd(self):
        # before we generate any tc_users, we expect there to be nothing to output:
        options = {'dest-from-settings': True}
        with self.settings(PEARSON={'LOCAL_EXPORT': self.export_dir}):
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 1, "Expect cdd file to have no non-header lines")
            os.remove(filepath)

            # generating a tc_user should result in a line in the output
            username = 'test_single_cdd'
            create_tc_user(username)
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 2, "Expect cdd file to have one non-header line")
            os.remove(filepath)

            # output after registration should not have any entries again.
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 1, "Expect cdd file to have no non-header lines")
            os.remove(filepath)

            # if we modify the record, then it should be output again:
            user_options = {'first_name': 'NewTestFirst', }
            call_command('pearson_make_tc_user', username, **user_options)
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 2, "Expect cdd file to have one non-header line")
            os.remove(filepath)

    def test_export_single_ead(self):
        # before we generate any registrations, we expect there to be nothing to output:
        options = {'dest-from-settings': True}
        with self.settings(PEARSON={'LOCAL_EXPORT': self.export_dir}):
            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 1, "Expect ead file to have no non-header lines")
            os.remove(filepath)

            # generating a registration should result in a line in the output
            username = 'test_single_ead'
            create_tc_user(username)
            create_tc_registration(username)
            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 2, "Expect ead file to have one non-header line")
            os.remove(filepath)

            # output after registration should not have any entries again.
            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 1, "Expect ead file to have no non-header lines")
            os.remove(filepath)

            # if we modify the record, then it should be output again:
            create_tc_registration(username, accommodation_code='EQPMNT')
            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 2, "Expect ead file to have one non-header line")
            os.remove(filepath)

    def test_export_multiple(self):
        create_multiple_registrations("export")
        with self.settings(PEARSON={'LOCAL_EXPORT': self.export_dir}):
            options = {'dest-from-settings': True}
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 5, "Expect cdd file to have four non-header lines: total was {}".format(numlines))
            os.remove(filepath)

            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 7, "Expect ead file to have six non-header lines: total was {}".format(numlines))
            os.remove(filepath)


#    def test_bad_demographic_option(self):
#        username = 'nonuser'
#        output_string, stderrmsg = get_error_string_for_management_call('pearson_make_tc_user', username, **{'--garbage' : None })
#        print stderrmsg
#        self.assertErrorContains(stderrmsg, 'Unexpected option')
#
#    def test_missing_demographic_user(self):
#        username = 'nonuser'
#        output_string, error_string = get_error_string_for_management_call('pearson_make_tc_user', username, **{})
#        self.assertErrorContains(error_string, 'User matching query does not exist')

# credentials for a test SFTP site:
SFTP_HOSTNAME = 'ec2-23-20-150-101.compute-1.amazonaws.com'
SFTP_USERNAME = 'pearsontest'
SFTP_PASSWORD = 'password goes here'

S3_BUCKET = 'edx-pearson-archive'
AWS_ACCESS_KEY_ID = 'put yours here'
AWS_SECRET_ACCESS_KEY = 'put yours here'


class PearsonTransferTestCase(PearsonTestCase):
    '''
    Class for tests running Pearson transfers
    '''

    def test_transfer_config(self):
        with self.settings(DATADOG_API='FAKE_KEY'):
            # TODO: why is this failing with the wrong error message?!
            stderrmsg = get_command_error_text('pearson_transfer', **{'mode': 'garbage'})
            self.assertErrorContains(stderrmsg, 'Error: No PEARSON entries')
        with self.settings(DATADOG_API='FAKE_KEY'):
            stderrmsg = get_command_error_text('pearson_transfer')
            self.assertErrorContains(stderrmsg, 'Error: No PEARSON entries')
        with self.settings(DATADOG_API='FAKE_KEY',
                           PEARSON={'LOCAL_EXPORT': self.export_dir,
                                    'LOCAL_IMPORT': self.import_dir}):
            stderrmsg = get_command_error_text('pearson_transfer')
            self.assertErrorContains(stderrmsg, 'Error: No entry in the PEARSON settings')

    def test_transfer_export_missing_dest_dir(self):
        raise SkipTest()
        create_multiple_registrations('export_missing_dest')
        with self.settings(DATADOG_API='FAKE_KEY',
                           PEARSON={'LOCAL_EXPORT': self.export_dir,
                                    'SFTP_EXPORT': 'this/does/not/exist',
                                    'SFTP_HOSTNAME': SFTP_HOSTNAME,
                                    'SFTP_USERNAME': SFTP_USERNAME,
                                    'SFTP_PASSWORD': SFTP_PASSWORD,
                                    'S3_BUCKET': S3_BUCKET,
                                    },
                           AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                           AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY):
            options = {'mode': 'export'}
            stderrmsg = get_command_error_text('pearson_transfer', **options)
            self.assertErrorContains(stderrmsg, 'Error: SFTP destination path does not exist')

    def test_transfer_export(self):
        raise SkipTest()
        create_multiple_registrations("transfer_export")
        with self.settings(DATADOG_API='FAKE_KEY',
                           PEARSON={'LOCAL_EXPORT': self.export_dir,
                                    'SFTP_EXPORT': 'results/topvue',
                                    'SFTP_HOSTNAME': SFTP_HOSTNAME,
                                    'SFTP_USERNAME': SFTP_USERNAME,
                                    'SFTP_PASSWORD': SFTP_PASSWORD,
                                    'S3_BUCKET': S3_BUCKET,
                                    },
                           AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                           AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY):
            options = {'mode': 'export'}
#            call_command('pearson_transfer', **options)
#            # confirm that the export directory is still empty:
#            self.assertEqual(len(os.listdir(self.export_dir)), 0, "expected export directory to be empty")

    def test_transfer_import_missing_source_dir(self):
        raise SkipTest()
        create_multiple_registrations('import_missing_src')
        with self.settings(DATADOG_API='FAKE_KEY',
                           PEARSON={'LOCAL_IMPORT': self.import_dir,
                                    'SFTP_IMPORT': 'this/does/not/exist',
                                    'SFTP_HOSTNAME': SFTP_HOSTNAME,
                                    'SFTP_USERNAME': SFTP_USERNAME,
                                    'SFTP_PASSWORD': SFTP_PASSWORD,
                                    'S3_BUCKET': S3_BUCKET,
                                    },
                           AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                           AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY):
            options = {'mode': 'import'}
            stderrmsg = get_command_error_text('pearson_transfer', **options)
            self.assertErrorContains(stderrmsg, 'Error: SFTP source path does not exist')

    def test_transfer_import(self):
        raise SkipTest()
        create_multiple_registrations('import_missing_src')
        with self.settings(DATADOG_API='FAKE_KEY',
                           PEARSON={'LOCAL_IMPORT': self.import_dir,
                                    'SFTP_IMPORT': 'results',
                                    'SFTP_HOSTNAME': SFTP_HOSTNAME,
                                    'SFTP_USERNAME': SFTP_USERNAME,
                                    'SFTP_PASSWORD': SFTP_PASSWORD,
                                    'S3_BUCKET': S3_BUCKET,
                                    },
                           AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                           AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY):
            options = {'mode': 'import'}
            call_command('pearson_transfer', **options)
            self.assertEqual(len(os.listdir(self.import_dir)), 0, "expected import directory to be empty")
