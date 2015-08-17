from unittest import skip

from django.contrib.auth.models import User

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.utils import AjaxEnabledTestClient


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
        super(InternationalizationTest, self).setUp(create_user=False)

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
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
        }

    def test_course_plain_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html('/home/')
        self.assertContains(resp,
                            '<h1 class="page-header">Studio Home</h1>',
                            status_code=200,
                            html=True)

    def test_course_explicit_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='en',
        )

        self.assertContains(resp,
                            '<h1 class="page-header">Studio Home</h1>',
                            status_code=200,
                            html=True)

    # ****
    # NOTE:
    # ****
    #
    # This test will break when we replace this fake 'test' language
    # with actual Esperanto. This test will need to be updated with
    # actual Esperanto at that time.
    # Test temporarily disable since it depends on creation of dummy strings
    @skip
    def test_course_with_accents(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='eo'
        )

        TEST_STRING = (
            u'<h1 class="title-1">'
            u'My \xc7\xf6\xfcrs\xe9s L#'
            u'</h1>'
        )

        self.assertContains(resp,
                            TEST_STRING,
                            status_code=200,
                            html=True)
