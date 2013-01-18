'''
Created on Jan 17, 2013

@author: brian
'''
import logging

from django.test import TestCase
from student.models import User, TestCenterRegistration, TestCenterUser
# This is stupid!  Because I import a function with the word "test" in the name,
# the unittest framework tries to run *it* as a test?!  Crazy!
from student.models import get_testcenter_registration as get_tc_registration
from django.core import management

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
        output_dir = "./tmpOutput"
        options = { 'destination' : output_dir }
        with self.settings(PEARSON={ 'LOCAL_EXPORT' : output_dir }):
            management.call_command('pearson_export_cdd', **options)
            management.call_command('pearson_export_ead', **options)
        # TODO: check that files were output....
        
