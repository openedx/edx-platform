"""
Tests for Shibboleth Authentication
@jbau
"""
import unittest

from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.base import SessionBase

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.django import modulestore

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE

from external_auth.models import ExternalAuthMap
from external_auth.views import shib_login, course_specific_login, course_specific_register

from student.views import create_account, change_enrollment
from student.models import UserProfile, Registration, CourseEnrollment
from student.tests.factories import UserFactory

#Shib is supposed to provide 'REMOTE_USER', 'givenName', 'sn', 'mail', 'Shib-Identity-Provider'
#attributes via request.META.  We can count on 'Shib-Identity-Provider', and 'REMOTE_USER' being present
#b/c of how mod_shib works but should test the behavior with the rest of the attributes present/missing

#For the sake of python convention we'll make all of these variable names ALL_CAPS
IDP = 'https://idp.stanford.edu/'
REMOTE_USER = 'test_user@stanford.edu'
MAILS = [None, '', 'test_user@stanford.edu']
GIVENNAMES = [None, '', 'Jason', 'jason; John; bob']  # At Stanford, the givenNames can be a list delimited by ';'
SNS = [None, '', 'Bau', 'bau; smith']  # At Stanford, the sns can be a list delimited by ';'


def gen_all_identities():
    """A generator for all combinations of identity inputs"""
    def _build_identity_dict(mail, given_name, surname):
        """ Helper function to return a dict of test identity """
        meta_dict = {}
        meta_dict.update({'Shib-Identity-Provider': IDP,
                          'REMOTE_USER': REMOTE_USER})
        if mail is not None:
            meta_dict.update({'mail': mail})
        if given_name is not None:
            meta_dict.update({'givenName': given_name})
        if surname is not None:
            meta_dict.update({'sn': surname})
        return meta_dict

    for mail in MAILS:
        for given_name in GIVENNAMES:
            for surname in SNS:
                yield _build_identity_dict(mail, given_name, surname)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ShibSPTest(ModuleStoreTestCase):
    """
    Tests for the Shibboleth SP, which communicates via request.META
    (Apache environment variables set by mod_shib)
    """
    factory = RequestFactory()

    def setUp(self):
        self.store = modulestore()

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_shib_login(self):
        """
        Tests that a user with a shib ExternalAuthMap gets logged in while when
        shib-login is called, while a user without such gets the registration form.
        """

        student = UserFactory.create()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=student)
        student.save()
        extauth.save()

        idps = ['https://idp.stanford.edu/', 'https://someother.idp.com/']
        remote_users = ['testuser@stanford.edu', 'testuser2@someother_idp.com']

        for idp in idps:
            for remote_user in remote_users:
                request = self.factory.get('/shib-login')
                request.session = SessionBase()  # empty session
                request.META.update({'Shib-Identity-Provider': idp,
                                     'REMOTE_USER': remote_user})
                request.user = AnonymousUser()
                response = shib_login(request)
                if idp == "https://idp.stanford.edu" and remote_user == 'testuser@stanford.edu':
                    self.assertIsInstance(response, HttpResponseRedirect)
                    self.assertEqual(request.user, student)
                    self.assertEqual(response['Location'], '/')
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "<title>Register for")

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_registration_form(self):
        """
        Tests the registration form showing up with the proper parameters.

        Uses django test client for its session support
        """
        for identity in gen_all_identities():
            self.client.logout()
            request_kwargs = {'path': '/shib-login/', 'data': {}, 'follow': False}
            request_kwargs.update(identity)
            response = self.client.get(**request_kwargs)  # identity k/v pairs will show up in request.META

            self.assertEquals(response.status_code, 200)
            mail_input_HTML = '<input class="" id="email" type="email" name="email"'
            if not identity.get('mail'):
                self.assertContains(response, mail_input_HTML)
            else:
                self.assertNotContains(response, mail_input_HTML)
            sn_empty = identity.get('sn', '') == ''
            given_name_empty = identity.get('givenName', '') == ''
            fullname_input_HTML = '<input id="name" type="text" name="name"'
            if sn_empty and given_name_empty:
                self.assertContains(response, fullname_input_HTML)
            else:
                self.assertNotContains(response, fullname_input_HTML)

            #clean up b/c we don't want existing ExternalAuthMap for the next run
            self.client.session['ExternalAuthMap'].delete()

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_registration_formSubmit(self):
        """
        Tests user creation after the registration form that pops is submitted.  If there is no shib
        ExternalAuthMap in the session, then the created user should take the username and email from the
        request.

        Uses django test client for its session support
        """
        for identity in gen_all_identities():
            #First we pop the registration form
            self.client.logout()
            request1_kwargs = {'path': '/shib-login/', 'data': {}, 'follow': False}
            request1_kwargs.update(identity)
            response1 = self.client.get(**request1_kwargs)
            #Then we have the user answer the registration form
            postvars = {'email': 'post_email@stanford.edu',
                        'username': 'post_username',
                        'password': 'post_password',
                        'name': 'post_name',
                        'terms_of_service': 'true',
                        'honor_code': 'true'}
            #use RequestFactory instead of TestClient here because we want access to request.user
            request2 = self.factory.post('/create_account', data=postvars)
            request2.session = self.client.session
            request2.user = AnonymousUser()
            response2 = create_account(request2)

            user = request2.user
            mail = identity.get('mail')
            #check that the created user has the right email, either taken from shib or user input
            if mail:
                self.assertEqual(user.email, mail)
                self.assertEqual(list(User.objects.filter(email=postvars['email'])), [])
                self.assertIsNotNone(User.objects.get(email=mail))  # get enforces only 1 such user
            else:
                self.assertEqual(user.email, postvars['email'])
                self.assertEqual(list(User.objects.filter(email=mail)), [])
                self.assertIsNotNone(User.objects.get(email=postvars['email']))  # get enforces only 1 such user

            #check that the created user profile has the right name, either taken from shib or user input
            profile = UserProfile.objects.get(user=user)
            sn_empty = identity.get('sn', '') == ''
            given_name_empty = identity.get('givenName', '') == ''
            if sn_empty and given_name_empty:
                self.assertEqual(profile.name, postvars['name'])
            else:
                self.assertEqual(profile.name, request2.session['ExternalAuthMap'].external_name)

            #clean up for next loop
            request2.session['ExternalAuthMap'].delete()
            UserProfile.objects.filter(user=user).delete()
            Registration.objects.filter(user=user).delete()
            user.delete()

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_course_specificLoginAndReg(self):
        """
        Tests that the correct course specific login and registration urls work for shib
        """
        course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')

        # Test for cases where course is found
        for domain in ["", "shib:https://idp.stanford.edu/"]:
            #set domains
            course.enrollment_domain = domain
            metadata = own_metadata(course)
            metadata['enrollment_domain'] = domain
            self.store.update_metadata(course.location.url(), metadata)

            #setting location to test that GET params get passed through
            login_request = self.factory.get('/course_specific_login/MITx/999/Robot_Super_Course' +
                                             '?course_id=MITx/999/Robot_Super_Course' +
                                             '&enrollment_action=enroll')
            reg_request = self.factory.get('/course_specific_register/MITx/999/Robot_Super_Course' +
                                           '?course_id=MITx/999/course/Robot_Super_Course' +
                                           '&enrollment_action=enroll')

            login_response = course_specific_login(login_request, 'MITx/999/Robot_Super_Course')
            reg_response = course_specific_register(login_request, 'MITx/999/Robot_Super_Course')

            if "shib" in domain:
                self.assertIsInstance(login_response, HttpResponseRedirect)
                self.assertEqual(login_response['Location'],
                                 reverse('shib-login') +
                                 '?course_id=MITx/999/Robot_Super_Course' +
                                 '&enrollment_action=enroll')
                self.assertIsInstance(login_response, HttpResponseRedirect)
                self.assertEqual(reg_response['Location'],
                                 reverse('shib-login') +
                                 '?course_id=MITx/999/Robot_Super_Course' +
                                 '&enrollment_action=enroll')
            else:
                self.assertIsInstance(login_response, HttpResponseRedirect)
                self.assertEqual(login_response['Location'],
                                 reverse('signin_user') +
                                 '?course_id=MITx/999/Robot_Super_Course' +
                                 '&enrollment_action=enroll')
                self.assertIsInstance(login_response, HttpResponseRedirect)
                self.assertEqual(reg_response['Location'],
                                 reverse('register_user') +
                                 '?course_id=MITx/999/Robot_Super_Course' +
                                 '&enrollment_action=enroll')

            # Now test for non-existent course
            #setting location to test that GET params get passed through
            login_request = self.factory.get('/course_specific_login/DNE/DNE/DNE' +
                                             '?course_id=DNE/DNE/DNE' +
                                             '&enrollment_action=enroll')
            reg_request = self.factory.get('/course_specific_register/DNE/DNE/DNE' +
                                           '?course_id=DNE/DNE/DNE/Robot_Super_Course' +
                                           '&enrollment_action=enroll')

            login_response = course_specific_login(login_request, 'DNE/DNE/DNE')
            reg_response = course_specific_register(login_request, 'DNE/DNE/DNE')

            self.assertIsInstance(login_response, HttpResponseRedirect)
            self.assertEqual(login_response['Location'],
                             reverse('signin_user') +
                             '?course_id=DNE/DNE/DNE' +
                             '&enrollment_action=enroll')
            self.assertIsInstance(login_response, HttpResponseRedirect)
            self.assertEqual(reg_response['Location'],
                             reverse('register_user') +
                             '?course_id=DNE/DNE/DNE' +
                             '&enrollment_action=enroll')

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_enrollment_limit_by_domain(self):
        """
            Tests that the enrollmentDomain setting is properly limiting enrollment to those who have
            the proper external auth
        """

        #create 2 course, one with limited enrollment one without
        course1 = CourseFactory.create(org='Stanford', number='123', display_name='Shib Only')
        course1.enrollment_domain = 'shib:https://idp.stanford.edu/'
        metadata = own_metadata(course1)
        metadata['enrollment_domain'] = course1.enrollment_domain
        self.store.update_metadata(course1.location.url(), metadata)

        course2 = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        course2.enrollment_domain = ''
        metadata = own_metadata(course2)
        metadata['enrollment_domain'] = course2.enrollment_domain
        self.store.update_metadata(course2.location.url(), metadata)

        # create 3 kinds of students, external_auth matching course1, external_auth not matching, no external auth
        student1 = UserFactory.create()
        student1.save()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=student1)
        extauth.save()

        student2 = UserFactory.create()
        student2.username = "teststudent2"
        student2.email = "teststudent2@other.edu"
        student2.save()
        extauth = ExternalAuthMap(external_id='testuser1@other.edu',
                                  external_email='',
                                  external_domain='shib:https://other.edu/',
                                  external_credentials="",
                                  user=student2)
        extauth.save()

        student3 = UserFactory.create()
        student3.username = "teststudent3"
        student3.email = "teststudent3@gmail.com"
        student3.save()

        #Tests the two case for courses, limited and not
        for course in [course1, course2]:
            for student in [student1, student2, student3]:
                request = self.factory.post('/change_enrollment')
                request.POST.update({'enrollment_action': 'enroll',
                                     'course_id': course.id})
                request.user = student
                response = change_enrollment(request)
                #if course is not limited or student has correct shib extauth then enrollment should be allowed
                if course is course2 or student is student1:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)
                    #clean up
                    CourseEnrollment.objects.filter(user=student, course_id=course.id).delete()
                else:
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_shib_login_enrollment(self):
        """
            A functionality test that a student with an existing shib login can auto-enroll in a class with GET params
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        student = UserFactory.create()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  internal_password="password",
                                  user=student)
        student.set_password("password")
        student.save()
        extauth.save()

        course = CourseFactory.create(org='Stanford', number='123', display_name='Shib Only')
        course.enrollment_domain = 'shib:https://idp.stanford.edu/'
        metadata = own_metadata(course)
        metadata['enrollment_domain'] = course.enrollment_domain
        self.store.update_metadata(course.location.url(), metadata)

        #use django test client for sessions and url processing
        #no enrollment before trying
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)
        self.client.logout()
        request_kwargs = {'path': '/shib-login/',
                          'data': {'enrollment_action': 'enroll', 'course_id': course.id},
                          'follow': False,
                          'REMOTE_USER': 'testuser@stanford.edu',
                          'Shib-Identity-Provider': 'https://idp.stanford.edu/'}
        response = self.client.get(**request_kwargs)
        #successful login is a redirect to "/"
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'http://testserver/')
        #now there is enrollment
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)
