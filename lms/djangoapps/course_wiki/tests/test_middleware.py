"""
Tests for wiki middleware.
"""


from django.test.client import Client
from wiki.models import URLPath
from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_AMNESTY_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import InstructorFactory
from lms.djangoapps.course_wiki.views import get_or_create_root


class TestWikiAccessMiddleware(ModuleStoreTestCase):
    """Tests for WikiAccessMiddleware."""
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE

    def setUp(self):
        """Test setup."""
        super().setUp()

        self.wiki = get_or_create_root()

        self.course_math101 = CourseFactory.create(org='edx', number='math101', display_name='2014', metadata={'use_unique_wiki_id': 'false'})  # lint-amnesty, pylint: disable=line-too-long
        self.course_math101_instructor = InstructorFactory(course_key=self.course_math101.id, username='instructor', password='secret')  # lint-amnesty, pylint: disable=line-too-long
        self.wiki_math101 = URLPath.create_article(self.wiki, 'math101', title='math101')

        self.client = Client()
        self.client.login(username='instructor', password='secret')

    def test_url_tranform(self):
        """Test that the correct prefix ('/courses/<course_id>') is added to the urls in the wiki."""
        response = self.client.get('/courses/edx/math101/2014/wiki/math101/')
        self.assertContains(response, '/courses/edx/math101/2014/wiki/math101/_edit/')
        self.assertContains(response, '/courses/edx/math101/2014/wiki/math101/_settings/')
