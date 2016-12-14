"""
Tests for wiki middleware.
"""
from django.conf import settings
from django.test.client import Client
from nose.plugins.attrib import attr
from wiki.models import URLPath

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme

from courseware.tests.factories import InstructorFactory
from course_wiki.views import get_or_create_root


@attr('shard_1')
class TestComprehensiveTheming(ModuleStoreTestCase):
    """Tests for comprehensive theming of wiki pages."""

    def setUp(self):
        """Test setup."""
        super(TestComprehensiveTheming, self).setUp()

        self.wiki = get_or_create_root()

        self.course_math101 = CourseFactory.create(org='edx', number='math101', display_name='2014',
                                                   metadata={'use_unique_wiki_id': 'false'})
        self.course_math101_instructor = InstructorFactory(course_key=self.course_math101.id, username='instructor',
                                                           password='secret')
        self.wiki_math101 = URLPath.create_article(self.wiki, 'math101', title='math101')

        self.client = Client()
        self.client.login(username='instructor', password='secret')

    @with_comprehensive_theme(settings.REPO_ROOT / 'themes/red-theme')
    def test_themed_footer(self):
        """
        Tests that theme footer is used rather than standard
        footer when comprehensive theme is enabled.
        """
        response = self.client.get('/courses/edx/math101/2014/wiki/math101/')
        self.assertEqual(response.status_code, 200)
        # This string comes from themes/red-theme/lms/templates/footer.html
        self.assertContains(response, "super-ugly")
