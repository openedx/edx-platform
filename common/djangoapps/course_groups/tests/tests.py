from nose import SkipTest
import django.test
from django.contrib.auth.models import User
from django.conf import settings

from override_settings import override_settings


from course_groups.models import CourseUserGroup
from course_groups.cohorts import get_cohort, get_course_cohorts

from xmodule.tests.test_import import BaseCourseTestCase
from xmodule.modulestore.django import modulestore

def xml_store_config(data_dir):
    return {
    'default': {
        'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
        'OPTIONS': {
            'data_dir': data_dir,
            'default_class': 'xmodule.hidden_module.HiddenDescriptor',
        }
    }
}

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestCohorts(django.test.TestCase):

    def test_get_cohort(self):
        # Need to fix this, but after we're testing on staging.  (Looks like
        # problem is that when get_cohort internally tries to look up the
        # course.id, it fails, even though we loaded it through the modulestore.

        # Proper fix: give all tests a standard modulestore that uses the test
        # dir.
        raise SkipTest()
        course = modulestore().get_course("edX/toy/2012_Fall")
        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                               group_type=CourseUserGroup.COHORT)

        user = User.objects.create(username="test", email="a@b.com")
        other_user = User.objects.create(username="test2", email="a2@b.com")

        cohort.users.add(user)

        got = get_cohort(user, course.id)
        self.assertEquals(got.id, cohort.id, "Should find the right cohort")

        got = get_cohort(other_user, course.id)
        self.assertEquals(got, None, "other_user shouldn't have a cohort")


    def test_get_course_cohorts(self):
        course1_id = 'a/b/c'
        course2_id = 'e/f/g'

        # add some cohorts to course 1
        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course1_id,
                                                group_type=CourseUserGroup.COHORT)

        cohort = CourseUserGroup.objects.create(name="TestCohort2",
                                                course_id=course1_id,
                                                group_type=CourseUserGroup.COHORT)


        # second course should have no cohorts
        self.assertEqual(get_course_cohorts(course2_id), [])

        cohorts = sorted([c.name for c in get_course_cohorts(course1_id)])
        self.assertEqual(cohorts, ['TestCohort', 'TestCohort2'])

