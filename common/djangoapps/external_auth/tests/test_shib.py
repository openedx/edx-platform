"""
Tests for Shibboleth Authentication
@jbau
"""
import unittest
from mock import patch

from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.client import RequestFactory, Client as DjangoTestClient
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User
from django.utils.importlib import import_module

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

# Shib is supposed to provide 'REMOTE_USER', 'givenName', 'sn', 'mail', 'Shib-Identity-Provider'
# attributes via request.META.  We can count on 'Shib-Identity-Provider', and 'REMOTE_USER' being present
# b/c of how mod_shib works but should test the behavior with the rest of the attributes present/missing

# For the sake of python convention we'll make all of these variable names ALL_CAPS
IDP = 'https://idp.stanford.edu/'
REMOTE_USER = 'test_user@stanford.edu'
MAILS = [None, '', 'test_user@stanford.edu']
GIVENNAMES = [None, '', 'Jason', 'jas\xc3\xb6n; John; bob']  # At Stanford, the givenNames can be a list delimited by ';'
SNS = [None, '', 'Bau', '\xe5\x8c\x85; smith']  # At Stanford, the sns can be a list delimited by ';'


def gen_all_identities():
    """
    A generator for all combinations of test inputs.
    Each generated item is a dict that represents what a shib IDP
    could potentially pass to django via request.META, i.e.
    setting (or not) request.META['givenName'], etc.
    """
    def _build_identity_dict(mail, given_name, surname):
        """ Helper function to return a dict of test identity """
        meta_dict = {'Shib-Identity-Provider': IDP,
                     'REMOTE_USER': REMOTE_USER}
        if mail is not None:
            meta_dict['mail'] = mail
        if given_name is not None:
            meta_dict['givenName'] = given_name
        if surname is not None:
            meta_dict['sn'] = surname
        return meta_dict

    for mail in MAILS:
        for given_name in GIVENNAMES:
            for surname in SNS:
                yield _build_identity_dict(mail, given_name, surname)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE, SESSION_ENGINE='django.contrib.sessions.backends.cache')
class ShibSPTest(ModuleStoreTestCase):
    """
    Tests for the Shibboleth SP, which communicates via request.META
    (Apache environment variables set by mod_shib)
    """
    request_factory = RequestFactory()

    def setUp(self):
        self.store = modulestore()

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_exception_shib_login(self):
        """
        Tests that we get the error page when there is no REMOTE_USER
        or Shib-Identity-Provider in request.META
        """
        no_remote_user_request = self.request_factory.get('/shib-login')
        no_remote_user_request.META.update({'Shib-Identity-Provider': IDP})
        no_remote_user_response = shib_login(no_remote_user_request)
        self.assertEqual(no_remote_user_response.status_code, 403)
        self.assertIn("identity server did not return your ID information", no_remote_user_response.content)

        no_idp_request = self.request_factory.get('/shib-login')
        no_idp_request.META.update({'REMOTE_USER': REMOTE_USER})
        no_idp_response = shib_login(no_idp_request)
        self.assertEqual(no_idp_response.status_code, 403)
        self.assertIn("identity server did not return your ID information", no_idp_response.content)

    def _assert_shib_login_is_logged(self, audit_log_call, remote_user):
        """Asserts that shibboleth login attempt is being logged"""
        method_name, args, _kwargs = audit_log_call
        self.assertEquals(method_name, 'info')
        self.assertEquals(len(args), 2)
        self.assertIn(u'logged in via Shibboleth', args[0])
        self.assertEquals(remote_user, args[1])

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_shib_login(self):
        """
        Tests that:
          * shib credentials that match an existing ExternalAuthMap with a linked active user logs the user in
          * shib credentials that match an existing ExternalAuthMap with a linked inactive user shows error page
          * shib credentials that match an existing ExternalAuthMap without a linked user and also match the email
            of an existing user without an existing ExternalAuthMap links the two and log the user in
          * shib credentials that match an existing ExternalAuthMap without a linked user and also match the email
            of an existing user that already has an ExternalAuthMap causes an error (403)
          * shib credentials that do not match an existing ExternalAuthMap causes the registration form to appear
        """

        user_w_map = UserFactory.create(email='withmap@stanford.edu')
        extauth = ExternalAuthMap(external_id='withmap@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=user_w_map)
        user_wo_map = UserFactory.create(email='womap@stanford.edu')
        user_w_map.save()
        user_wo_map.save()
        extauth.save()

        inactive_user = UserFactory.create(email='inactive@stanford.edu')
        inactive_user.is_active = False
        inactive_extauth = ExternalAuthMap(external_id='inactive@stanford.edu',
                                           external_email='',
                                           external_domain='shib:https://idp.stanford.edu/',
                                           external_credentials="",
                                           user=inactive_user)
        inactive_user.save()
        inactive_extauth.save()

        idps = ['https://idp.stanford.edu/', 'https://someother.idp.com/']
        remote_users = ['withmap@stanford.edu', 'womap@stanford.edu',
                        'testuser2@someother_idp.com', 'inactive@stanford.edu']

        for idp in idps:
            for remote_user in remote_users:
                request = self.request_factory.get('/shib-login')
                request.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
                request.META.update({'Shib-Identity-Provider': idp,
                                     'REMOTE_USER': remote_user,
                                     'mail': remote_user})
                request.user = AnonymousUser()
                with patch('external_auth.views.AUDIT_LOG') as mock_audit_log:
                    response = shib_login(request)
                audit_log_calls = mock_audit_log.method_calls

                if idp == "https://idp.stanford.edu/" and remote_user == 'withmap@stanford.edu':
                    self.assertIsInstance(response, HttpResponseRedirect)
                    self.assertEqual(request.user, user_w_map)
                    self.assertEqual(response['Location'], '/')
                    # verify logging:
                    self.assertEquals(len(audit_log_calls), 2)
                    self._assert_shib_login_is_logged(audit_log_calls[0], remote_user)
                    method_name, args, _kwargs = audit_log_calls[1]
                    self.assertEquals(method_name, 'info')
                    self.assertEquals(len(args), 3)
                    self.assertIn(u'Login success', args[0])
                    self.assertEquals(remote_user, args[2])
                elif idp == "https://idp.stanford.edu/" and remote_user == 'inactive@stanford.edu':
                    self.assertEqual(response.status_code, 403)
                    self.assertIn("Account not yet activated: please look for link in your email", response.content)
                    # verify logging:
                    self.assertEquals(len(audit_log_calls), 2)
                    self._assert_shib_login_is_logged(audit_log_calls[0], remote_user)
                    method_name, args, _kwargs = audit_log_calls[1]
                    self.assertEquals(method_name, 'warning')
                    self.assertEquals(len(args), 2)
                    self.assertIn(u'is not active after external login', args[0])
                    # self.assertEquals(remote_user, args[1])
                elif idp == "https://idp.stanford.edu/" and remote_user == 'womap@stanford.edu':
                    self.assertIsNotNone(ExternalAuthMap.objects.get(user=user_wo_map))
                    self.assertIsInstance(response, HttpResponseRedirect)
                    self.assertEqual(request.user, user_wo_map)
                    self.assertEqual(response['Location'], '/')
                    # verify logging:
                    self.assertEquals(len(audit_log_calls), 2)
                    self._assert_shib_login_is_logged(audit_log_calls[0], remote_user)
                    method_name, args, _kwargs = audit_log_calls[1]
                    self.assertEquals(method_name, 'info')
                    self.assertEquals(len(args), 3)
                    self.assertIn(u'Login success', args[0])
                    self.assertEquals(remote_user, args[2])
                elif idp == "https://someother.idp.com/" and remote_user in \
                            ['withmap@stanford.edu', 'womap@stanford.edu', 'inactive@stanford.edu']:
                    self.assertEqual(response.status_code, 403)
                    self.assertIn("You have already created an account using an external login", response.content)
                    # no audit logging calls
                    self.assertEquals(len(audit_log_calls), 0)
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "<title>Register for")
                    # no audit logging calls
                    self.assertEquals(len(audit_log_calls), 0)

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_registration_form(self):
        """
        Tests the registration form showing up with the proper parameters.

        Uses django test client for its session support
        """
        for identity in gen_all_identities():
            client = DjangoTestClient()
            # identity k/v pairs will show up in request.META
            response = client.get(path='/shib-login/', data={}, follow=False, **identity)

            self.assertEquals(response.status_code, 200)
            mail_input_HTML = '<input class="" id="email" type="email" name="email"'
            if not identity.get('mail'):
                self.assertContains(response, mail_input_HTML)
            else:
                self.assertNotContains(response, mail_input_HTML)
            sn_empty = not identity.get('sn')
            given_name_empty = not identity.get('givenName')
            fullname_input_HTML = '<input id="name" type="text" name="name"'
            if sn_empty and given_name_empty:
                self.assertContains(response, fullname_input_HTML)
            else:
                self.assertNotContains(response, fullname_input_HTML)

            # clean up b/c we don't want existing ExternalAuthMap for the next run
            client.session['ExternalAuthMap'].delete()

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_registration_formSubmit(self):
        """
        Tests user creation after the registration form that pops is submitted.  If there is no shib
        ExternalAuthMap in the session, then the created user should take the username and email from the
        request.

        Uses django test client for its session support
        """
        for identity in gen_all_identities():
            # First we pop the registration form
            client = DjangoTestClient()
            response1 = client.get(path='/shib-login/', data={}, follow=False, **identity)
            # Then we have the user answer the registration form
            postvars = {'email': 'post_email@stanford.edu',
                        'username': 'post_username',
                        'password': 'post_password',
                        'name': 'post_name',
                        'terms_of_service': 'true',
                        'honor_code': 'true'}
            # use RequestFactory instead of TestClient here because we want access to request.user
            request2 = self.request_factory.post('/create_account', data=postvars)
            request2.session = client.session
            request2.user = AnonymousUser()
            with patch('student.views.AUDIT_LOG') as mock_audit_log:
                _response2 = create_account(request2)

            user = request2.user
            mail = identity.get('mail')

            # verify logging of login happening during account creation:
            audit_log_calls = mock_audit_log.method_calls
            self.assertEquals(len(audit_log_calls), 3)
            method_name, args, _kwargs = audit_log_calls[0]
            self.assertEquals(method_name, 'info')
            self.assertEquals(len(args), 1)
            self.assertIn(u'Login success on new account creation', args[0])
            self.assertIn(u'post_username', args[0])
            method_name, args, _kwargs = audit_log_calls[1]
            self.assertEquals(method_name, 'info')
            self.assertEquals(len(args), 2)
            self.assertIn(u'User registered with external_auth', args[0])
            self.assertEquals(u'post_username', args[1])
            method_name, args, _kwargs = audit_log_calls[2]
            self.assertEquals(method_name, 'info')
            self.assertEquals(len(args), 3)
            self.assertIn(u'Updated ExternalAuthMap for ', args[0])
            self.assertEquals(u'post_username', args[1])
            self.assertEquals(u'test_user@stanford.edu', args[2].external_id)

            # check that the created user has the right email, either taken from shib or user input
            if mail:
                self.assertEqual(user.email, mail)
                self.assertEqual(list(User.objects.filter(email=postvars['email'])), [])
                self.assertIsNotNone(User.objects.get(email=mail))  # get enforces only 1 such user
            else:
                self.assertEqual(user.email, postvars['email'])
                self.assertEqual(list(User.objects.filter(email=mail)), [])
                self.assertIsNotNone(User.objects.get(email=postvars['email']))  # get enforces only 1 such user

            # check that the created user profile has the right name, either taken from shib or user input
            profile = UserProfile.objects.get(user=user)
            sn_empty = not identity.get('sn')
            given_name_empty = not identity.get('givenName')
            if sn_empty and given_name_empty:
                self.assertEqual(profile.name, postvars['name'])
            else:
                self.assertEqual(profile.name, request2.session['ExternalAuthMap'].external_name)
            # clean up for next loop
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
            # set domains
            course.enrollment_domain = domain
            metadata = own_metadata(course)
            metadata['enrollment_domain'] = domain
            self.store.update_metadata(course.location.url(), metadata)

            # setting location to test that GET params get passed through
            login_request = self.request_factory.get('/course_specific_login/MITx/999/Robot_Super_Course' +
                                                     '?course_id=MITx/999/Robot_Super_Course' +
                                                     '&enrollment_action=enroll')
            _reg_request = self.request_factory.get('/course_specific_register/MITx/999/Robot_Super_Course' +
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
            # setting location to test that GET params get passed through
            login_request = self.request_factory.get('/course_specific_login/DNE/DNE/DNE' +
                                                     '?course_id=DNE/DNE/DNE' +
                                                     '&enrollment_action=enroll')
            _reg_request = self.request_factory.get('/course_specific_register/DNE/DNE/DNE' +
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

        # create 2 course, one with limited enrollment one without
        shib_course = CourseFactory.create(org='Stanford', number='123', display_name='Shib Only')
        shib_course.enrollment_domain = 'shib:https://idp.stanford.edu/'
        metadata = own_metadata(shib_course)
        metadata['enrollment_domain'] = shib_course.enrollment_domain
        self.store.update_metadata(shib_course.location.url(), metadata)

        open_enroll_course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        open_enroll_course.enrollment_domain = ''
        metadata = own_metadata(open_enroll_course)
        metadata['enrollment_domain'] = open_enroll_course.enrollment_domain
        self.store.update_metadata(open_enroll_course.location.url(), metadata)

        # create 3 kinds of students, external_auth matching shib_course, external_auth not matching, no external auth
        shib_student = UserFactory.create()
        shib_student.save()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=shib_student)
        extauth.save()

        other_ext_student = UserFactory.create()
        other_ext_student.username = "teststudent2"
        other_ext_student.email = "teststudent2@other.edu"
        other_ext_student.save()
        extauth = ExternalAuthMap(external_id='testuser1@other.edu',
                                  external_email='',
                                  external_domain='shib:https://other.edu/',
                                  external_credentials="",
                                  user=other_ext_student)
        extauth.save()

        int_student = UserFactory.create()
        int_student.username = "teststudent3"
        int_student.email = "teststudent3@gmail.com"
        int_student.save()

        # Tests the two case for courses, limited and not
        for course in [shib_course, open_enroll_course]:
            for student in [shib_student, other_ext_student, int_student]:
                request = self.request_factory.post('/change_enrollment')
                request.POST.update({'enrollment_action': 'enroll',
                                     'course_id': course.id})
                request.user = student
                response = change_enrollment(request)
                # If course is not limited or student has correct shib extauth then enrollment should be allowed
                if course is open_enroll_course or student is shib_student:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)
                    # Clean up
                    CourseEnrollment.objects.filter(user=student, course_id=course.id).delete()
                else:
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)

    @unittest.skipUnless(settings.MITX_FEATURES.get('AUTH_USE_SHIB'), True)
    def test_shib_login_enrollment(self):
        """
            A functionality test that a student with an existing shib login can auto-enroll in a class with GET params
        """
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

        # use django test client for sessions and url processing
        # no enrollment before trying
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)
        self.client.logout()
        request_kwargs = {'path': '/shib-login/',
                          'data': {'enrollment_action': 'enroll', 'course_id': course.id},
                          'follow': False,
                          'REMOTE_USER': 'testuser@stanford.edu',
                          'Shib-Identity-Provider': 'https://idp.stanford.edu/'}
        response = self.client.get(**request_kwargs)
        # successful login is a redirect to "/"
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'http://testserver/')
        # now there is enrollment
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)
