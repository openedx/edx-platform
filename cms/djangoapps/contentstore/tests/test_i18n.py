from unittest import skip

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.client import Client

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class InternationalizationTest(ModuleStoreTestCase):
    """
    Tests to validate Internationalization.
    """

    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        self.uname = 'testuser'
        self.email = 'test+courses@edx.org'
        self.password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(self.uname, self.email, self.password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
        }

    def test_course_plain_english(self):
        """Test viewing the index page with no courses"""
        self.client = Client()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get(reverse('index'))
        self.assertContains(resp,
                            '<h1 class="page-header">My Courses</h1>',
                            status_code=200,
                            html=True)

    def test_course_explicit_english(self):
        """Test viewing the index page with no courses"""
        self.client = Client()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get(reverse('index'),
                               {},
                               HTTP_ACCEPT_LANGUAGE='en'
                               )

        self.assertContains(resp,
                            '<h1 class="page-header">My Courses</h1>',
                            status_code=200,
                            html=True)

    # ****
    # NOTE:
    # ****
    #
    # This test will break when we replace this fake 'test' language
    # with actual French. This test will need to be updated with
    # actual French at that time.
    # Test temporarily disable since it depends on creation of dummy strings
    @skip
    def test_course_with_accents(self):
        """Test viewing the index page with no courses"""
        self.client = Client()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get(reverse('index'),
                               {},
                               HTTP_ACCEPT_LANGUAGE='fr'
                               )

        TEST_STRING = u'<h1 class="title-1">' \
                      + u'My \xc7\xf6\xfcrs\xe9s L#' \
                      + u'</h1>'

        self.assertContains(resp,
                            TEST_STRING,
                            status_code=200,
                            html=True)
