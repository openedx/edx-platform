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
from django.core import management

from student.models import User, TestCenterRegistration, TestCenterUser, get_tc_registration

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
    management.call_command('pearson_make_tc_user', username, **options)
    return TestCenterUser.objects.get(user=user)
    
    
def create_tc_registration(username, course_id, exam_code, accommodation_code):
    
    options = { 'exam_series_code' : exam_code,
               'eligibility_appointment_date_first' : '2013-01-01T00:00',
               'eligibility_appointment_date_last' : '2013-12-31T23:59',
               'accommodation_code' : accommodation_code, 
               }

    management.call_command('pearson_make_tc_registration', username, course_id, **options)
    user = User.objects.get(username=username)
    registrations = get_tc_registration(user, course_id, exam_code)
    return registrations[0]
    
class PearsonTestCase(TestCase):
    '''
    Base class for tests running Pearson-related commands
    '''
    import_dir = mkdtemp(prefix="import")
    export_dir = mkdtemp(prefix="export")
    
    
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
        old_stdout = sys.stdout
        sys.stdout = cStringIO.StringIO()
        username = 'baduser'
        User.objects.create_user(username, '{}@edx.org'.format(username), 'fakepass')
        options = {}
               
        self.assertRaises(BaseException, management.call_command, 'pearson_make_tc_user', username, **options)
        output_string = sys.stdout.getvalue()
        self.assertTrue(output_string.find('Field Form errors encountered:') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  city') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  first_name') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  last_name') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  country') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  phone_country_code') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  phone') >= 0)
        self.assertTrue(output_string.find('Field Form Error:  address_1') >= 0)
        sys.stdout = old_stdout
        
    def test_create_good_testcenter_user(self):
        testcenter_user = create_tc_user("test1")
        
    def test_create_good_testcenter_registration(self):
        username = 'test1'
        course_id = 'org1/course1/term1'
        exam_code = 'exam1'
        accommodation_code = 'NONE'
        testcenter_user = create_tc_user(username)
        registration = create_tc_registration(username, course_id, exam_code, accommodation_code)
        
    def test_export(self):
        username = 'test1'
        course_id = 'org1/course1/term1'
        exam_code = 'exam1'
        accommodation_code = 'NONE'
        testcenter_user = create_tc_user(username)
        registration = create_tc_registration(username, course_id, exam_code, accommodation_code)
        #options = { 'destination' : self.export_dir }
        options = { '--dest-from-settings' : None }
        with self.settings(PEARSON={ 'LOCAL_EXPORT' : self.export_dir }):
            management.call_command('pearson_export_cdd', **options)
            print 'Files found: {}'.format(os.listdir(self.export_dir))
            self.assertEquals(len(os.listdir(self.export_dir)), 1, "Expect cdd file to be created")
            management.call_command('pearson_export_ead', **options)
            print 'Files found: {}'.format(os.listdir(self.export_dir))
            self.assertEquals(len(os.listdir(self.export_dir)), 2, "Expect ead file to also be created")

        # TODO: check that files were output....
        
