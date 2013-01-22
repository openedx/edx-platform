'''
Created on Jan 17, 2013

@author: brian
'''
import logging
import os
from tempfile import mkdtemp
import cStringIO
import sys

from django.test import TestCase
from django.core.management import call_command

from student.models import User, TestCenterRegistration, TestCenterUser, get_testcenter_registration

log = logging.getLogger(__name__)


def create_tc_user(username):
    user = User.objects.create_user(username, '{}@edx.org'.format(username), 'fakepass')
    options = {
                   'first_name' : 'TestFirst',
                   'last_name' : 'TestLast',
                   'address_1' : 'Test Address',
                   'city' : 'TestCity',
                   'state' : 'Alberta',
                   'postal_code' : 'A0B 1C2',
                   'country' : 'CAN',
                   'phone' : '252-1866',
                   'phone_country_code' : '1',
                    }
    call_command('pearson_make_tc_user', username, **options)
    return TestCenterUser.objects.get(user=user)
    
    
def create_tc_registration(username, course_id = 'org1/course1/term1', exam_code = 'exam1', accommodation_code = None):
    
    options = { 'exam_series_code' : exam_code,
               'eligibility_appointment_date_first' : '2013-01-01T00:00',
               'eligibility_appointment_date_last' : '2013-12-31T23:59',
               'accommodation_code' : accommodation_code, 
               }

    call_command('pearson_make_tc_registration', username, course_id, **options)
    user = User.objects.get(username=username)
    registrations = get_testcenter_registration(user, course_id, exam_code)
    return registrations[0]

def get_error_string_for_management_call(*args, **options):
    stdout_string = None
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = cStringIO.StringIO()
    sys.stderr = cStringIO.StringIO()
    try:
        call_command(*args, **options)
    except BaseException, why1:
        # The goal here is to catch CommandError calls.
        # But these are actually translated into nice messages,
        # and sys.exit(1) is then called.  For testing, we
        # want to catch what sys.exit throws, and get the
        # relevant text either from stdout or stderr. 
        # TODO: this should really check to see that we
        # arrived here because of a sys.exit(1).  Otherwise
        # we should just raise the exception.
        stdout_string = sys.stdout.getvalue()
        stderr_string = sys.stderr.getvalue()
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
        raise Exception("Expected to find a single file in {}, but found {}".format(dirpath,filelist))
            
class PearsonTestCase(TestCase):
    '''
    Base class for tests running Pearson-related commands
    '''
    import_dir = mkdtemp(prefix="import")
    export_dir = mkdtemp(prefix="export")
    
    def assertErrorContains(self, error_message, expected):
        self.assertTrue(error_message.find(expected) >= 0, 'error message "{}" did not contain "{}"'.format(error_message, expected))
        
    def tearDown(self):
        def delete_temp_dir(dirname):
            if os.path.exists(dirname):
                for filename in os.listdir(dirname):
                    os.remove(os.path.join(dirname, filename))
                os.rmdir(dirname)
            
        # clean up after any test data was dumped to temp directory
        delete_temp_dir(self.import_dir)
        delete_temp_dir(self.export_dir)

    def test_missing_demographic_fields(self):
        # We won't bother to test all details of form validation here.  
        # It is enough to show that it works here, but deal with test cases for the form
        # validation in the student tests, not these management tests.
        username = 'baduser'
        User.objects.create_user(username, '{}@edx.org'.format(username), 'fakepass')
        options = {}
        output_string, _ = get_error_string_for_management_call('pearson_make_tc_user', username, **options) 
        self.assertTrue(output_string.find('Field Form errors encountered:') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  city') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  first_name') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  last_name') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  country') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  phone_country_code') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  phone') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  address_1') >= 0)
        self.assertErrorContains(output_string, 'Field Form Error:  address_1')
        
    def test_create_good_testcenter_user(self):
        testcenter_user = create_tc_user("test1")
        self.assertIsNotNone(testcenter_user)
        
    def test_create_good_testcenter_registration(self):
        username = 'test1'
        create_tc_user(username)
        registration = create_tc_registration(username)
        self.assertIsNotNone(registration)

    def test_cdd_missing_option(self):
        _, error_string = get_error_string_for_management_call('pearson_export_cdd', **{})
        self.assertErrorContains(error_string, 'Error: --destination or --dest-from-settings must be used')
   
    def test_ead_missing_option(self):
        _, error_string = get_error_string_for_management_call('pearson_export_ead', **{})
        self.assertErrorContains(error_string, 'Error: --destination or --dest-from-settings must be used')

    def test_export_single_cdd(self):
        # before we generate any tc_users, we expect there to be nothing to output:
        options = { 'dest-from-settings' : True }
        with self.settings(PEARSON={ 'LOCAL_EXPORT' : self.export_dir }):
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
            user_options = { 'first_name' : 'NewTestFirst', }
            call_command('pearson_make_tc_user', username, **user_options)
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 2, "Expect cdd file to have one non-header line")
            os.remove(filepath)
            
    def test_export_single_ead(self):
        # before we generate any registrations, we expect there to be nothing to output:
        options = { 'dest-from-settings' : True }
        with self.settings(PEARSON={ 'LOCAL_EXPORT' : self.export_dir }):
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
        username1 = 'test_multiple1'
        create_tc_user(username1)
        create_tc_registration(username1)
        create_tc_registration(username1, course_id = 'org1/course2/term1')
        create_tc_registration(username1, exam_code = 'exam2')
        username2 = 'test_multiple2'
        create_tc_user(username2)
        create_tc_registration(username2)
        username3 = 'test_multiple3'
        create_tc_user(username3)
        create_tc_registration(username3, course_id = 'org1/course2/term1')
        username4 = 'test_multiple4'
        create_tc_user(username4)
        create_tc_registration(username4, exam_code = 'exam2')

        with self.settings(PEARSON={ 'LOCAL_EXPORT' : self.export_dir }):
            options = { 'dest-from-settings' : True }
            call_command('pearson_export_cdd', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 5, "Expect cdd file to have four non-header lines: total was {}".format(numlines))
            os.remove(filepath)

            call_command('pearson_export_ead', **options)
            (filepath, numlines) = get_file_info(self.export_dir)
            self.assertEquals(numlines, 7, "Expect ead file to have six non-header lines: total was {}".format(numlines))
            os.remove(filepath)


