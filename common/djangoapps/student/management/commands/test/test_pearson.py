'''
Created on Jan 17, 2013

@author: brian
'''
import logging

from django.test import TestCase
from student.models import User, TestCenterRegistration, TestCenterUser, unique_id_for_user
from mock import Mock
from datetime import datetime
from django.core import management

COURSE_1 = 'edX/toy/2012_Fall'
COURSE_2 = 'edx/full/6.002_Spring_2012'

log = logging.getLogger(__name__)

class PearsonTestCase(TestCase):
    '''
    Base class for tests running Pearson-related commands
    '''

    def test_create_good_testcenter_user(self):
        username = "rusty"
#        user = Mock(username=username)
#        # id = unique_id_for_user(user)
#        course = Mock(end_of_course_survey_url=survey_url)


        newuser = User.objects.create_user(username, 'rusty@edx.org', 'fakepass')
#        newuser.first_name='Rusty'
#        newuser.last_name='Skids'
#        newuser.is_staff=True
#        newuser.is_active=True
#        newuser.is_superuser=True
#        newuser.last_login=datetime(2012, 1, 1)
#        newuser.date_joined=datetime(2011, 1, 1)

#        newuser.save(using='default')
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
        management.call_command('pearson_make_tc_user', username, options)
        