"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
from datetime import datetime
from hashlib import sha1

from django.test import TestCase
from mock import patch, Mock
from nose.plugins.skip import SkipTest

from .models import User, UserProfile, CourseEnrollment, replicate_user, USER_FIELDS_TO_COPY
from .views import process_survey_link, _cert_info, unique_id_for_user

COURSE_1 = 'edX/toy/2012_Fall'
COURSE_2 = 'edx/full/6.002_Spring_2012'

log = logging.getLogger(__name__)

class ReplicationTest(TestCase):

    multi_db = True

    def test_user_replication(self):
        """Test basic user replication."""
        raise SkipTest()
        portal_user = User.objects.create_user('rusty', 'rusty@edx.org', 'fakepass')
        portal_user.first_name='Rusty'
        portal_user.last_name='Skids'
        portal_user.is_staff=True
        portal_user.is_active=True
        portal_user.is_superuser=True
        portal_user.last_login=datetime(2012, 1, 1)
        portal_user.date_joined=datetime(2011, 1, 1)
        # This is an Askbot field and will break if askbot is not included

        if hasattr(portal_user, 'seen_response_count'):
            portal_user.seen_response_count = 10

        portal_user.save(using='default')

        # We replicate this user to Course 1, then pull the same user and verify
        # that the fields copied over properly.
        replicate_user(portal_user, COURSE_1)
        course_user = User.objects.using(COURSE_1).get(id=portal_user.id)

        # Make sure the fields we care about got copied over for this user.
        for field in USER_FIELDS_TO_COPY:
            self.assertEqual(getattr(portal_user, field),
                             getattr(course_user, field),
                             "{0} not copied from {1} to {2}".format(
                                 field, portal_user, course_user
                             ))

        # This hasattr lameness is here because we don't want this test to be
        # triggered when we're being run by CMS tests (Askbot doesn't exist
        # there, so the test will fail).
        #
        # seen_response_count isn't a field we care about, so it shouldn't have
        # been copied over.
        if hasattr(portal_user, 'seen_response_count'):
            portal_user.seen_response_count = 20
            replicate_user(portal_user, COURSE_1)
            course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
            self.assertEqual(portal_user.seen_response_count, 20)
            self.assertEqual(course_user.seen_response_count, 0)

        # Another replication should work for an email change however, since
        # it's a field we care about.
        portal_user.email = "clyde@edx.org"
        replicate_user(portal_user, COURSE_1)
        course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
        self.assertEqual(portal_user.email, course_user.email)

        # During this entire time, the user data should never have made it over
        # to COURSE_2
        self.assertRaises(User.DoesNotExist,
                          User.objects.using(COURSE_2).get,
                          id=portal_user.id)


    def test_enrollment_for_existing_user_info(self):
        """Test the effect of Enrolling in a class if you've already got user
        data to be copied over."""
        raise SkipTest()
        # Create our User
        portal_user = User.objects.create_user('jack', 'jack@edx.org', 'fakepass')
        portal_user.first_name = "Jack"
        portal_user.save()

        # Set up our UserProfile info
        portal_user_profile = UserProfile.objects.create(
                                  user=portal_user,
                                  name="Jack Foo",
                                  level_of_education=None,
                                  gender='m',
                                  mailing_address=None,
                                  goals="World domination",
                              )
        portal_user_profile.save()

        # Now let's see if creating a CourseEnrollment copies all the relevant
        # data.
        portal_enrollment = CourseEnrollment.objects.create(user=portal_user,
                                                            course_id=COURSE_1)
        portal_enrollment.save()

        # Grab all the copies we expect
        course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
        self.assertEquals(portal_user, course_user)
        self.assertRaises(User.DoesNotExist,
                          User.objects.using(COURSE_2).get,
                          id=portal_user.id)

        course_enrollment = CourseEnrollment.objects.using(COURSE_1).get(id=portal_enrollment.id)
        self.assertEquals(portal_enrollment, course_enrollment)
        self.assertRaises(CourseEnrollment.DoesNotExist,
                          CourseEnrollment.objects.using(COURSE_2).get,
                          id=portal_enrollment.id)

        course_user_profile = UserProfile.objects.using(COURSE_1).get(id=portal_user_profile.id)
        self.assertEquals(portal_user_profile, course_user_profile)
        self.assertRaises(UserProfile.DoesNotExist,
                          UserProfile.objects.using(COURSE_2).get,
                          id=portal_user_profile.id)

        log.debug("Make sure our seen_response_count is not replicated.")
        if hasattr(portal_user, 'seen_response_count'):
            portal_user.seen_response_count = 200
            course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
            self.assertEqual(portal_user.seen_response_count, 200)
            self.assertEqual(course_user.seen_response_count, 0)
            portal_user.save()

            course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
            self.assertEqual(portal_user.seen_response_count, 200)
            self.assertEqual(course_user.seen_response_count, 0)

            portal_user.email = 'jim@edx.org'
            portal_user.save()
            course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
            self.assertEqual(portal_user.email, 'jim@edx.org')
            self.assertEqual(course_user.email, 'jim@edx.org')



    def test_enrollment_for_user_info_after_enrollment(self):
        """Test the effect of modifying User data after you've enrolled."""
        raise SkipTest()

        # Create our User
        portal_user = User.objects.create_user('patty', 'patty@edx.org', 'fakepass')
        portal_user.first_name = "Patty"
        portal_user.save()

        # Set up our UserProfile info
        portal_user_profile = UserProfile.objects.create(
                                  user=portal_user,
                                  name="Patty Foo",
                                  level_of_education=None,
                                  gender='f',
                                  mailing_address=None,
                                  goals="World peace",
                              )
        portal_user_profile.save()

        # Now let's see if creating a CourseEnrollment copies all the relevant
        # data when things are saved.
        portal_enrollment = CourseEnrollment.objects.create(user=portal_user,
                                                            course_id=COURSE_1)
        portal_enrollment.save()

        portal_user.last_name = "Bar"
        portal_user.save()
        portal_user_profile.gender = 'm'
        portal_user_profile.save()

        # Grab all the copies we expect, and make sure it doesn't end up in
        # places we don't expect.
        course_user = User.objects.using(COURSE_1).get(id=portal_user.id)
        self.assertEquals(portal_user, course_user)
        self.assertRaises(User.DoesNotExist,
                          User.objects.using(COURSE_2).get,
                          id=portal_user.id)

        course_enrollment = CourseEnrollment.objects.using(COURSE_1).get(id=portal_enrollment.id)
        self.assertEquals(portal_enrollment, course_enrollment)
        self.assertRaises(CourseEnrollment.DoesNotExist,
                          CourseEnrollment.objects.using(COURSE_2).get,
                          id=portal_enrollment.id)

        course_user_profile = UserProfile.objects.using(COURSE_1).get(id=portal_user_profile.id)
        self.assertEquals(portal_user_profile, course_user_profile)
        self.assertRaises(UserProfile.DoesNotExist,
                          UserProfile.objects.using(COURSE_2).get,
                          id=portal_user_profile.id)


class CourseEndingTest(TestCase):
    """Test things related to course endings: certificates, surveys, etc"""

    def test_process_survey_link(self):
        username = "fred"
        user = Mock(username=username)
        id = unique_id_for_user(user)
        link1 = "http://www.mysurvey.com"
        self.assertEqual(process_survey_link(link1, user), link1)

        link2 = "http://www.mysurvey.com?unique={UNIQUE_ID}"
        link2_expected = "http://www.mysurvey.com?unique={UNIQUE_ID}".format(UNIQUE_ID=id)
        self.assertEqual(process_survey_link(link2, user), link2_expected)

    def test_cert_info(self):
        user = Mock(username="fred")
        survey_url = "http://a_survey.com"
        course = Mock(end_of_course_survey_url=survey_url)

        self.assertEqual(_cert_info(user, course, None),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,})

        cert_status = {'status': 'unavailable'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False})

        cert_status = {'status': 'generating', 'grade': '67'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        cert_status = {'status': 'regenerating', 'grade': '67'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        download_url = 'http://s3.edx/cert'
        cert_status = {'status': 'downloadable', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'ready',
                          'show_disabled_download_button': False,
                          'show_download_url': True,
                          'download_url': download_url,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course2, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'grade': '67'
                          })
