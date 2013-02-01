import django.test
from django.contrib.auth.models import User
from django.conf import settings

from override_settings import override_settings

from course_groups.models import CourseUserGroup
from course_groups.cohorts import (get_cohort, get_course_cohorts,
                                   is_commentable_cohorted)

from xmodule.modulestore.django import modulestore, _MODULESTORES

# NOTE: running this with the lms.envs.test config works without
# manually overriding the modulestore.  However, running with
# cms.envs.test doesn't.  

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


    @staticmethod
    def topic_name_to_id(course, name):
        """
        Given a discussion topic name, return an id for that name (includes
        course and url_name).
        """
        return "{course}_{run}_{name}".format(course=course.location.course,
                                              run=course.url_name,
                                              name=name)


    @staticmethod
    def config_course_cohorts(course, discussions,
                              cohorted, cohorted_discussions=None):
        """
        Given a course with no discussion set up, add the discussions and set
        the cohort config appropriately.

        Arguments:
            course: CourseDescriptor
            discussions: list of topic names strings.  Picks ids and sort_keys
                automatically.
            cohorted: bool.
            cohorted_discussions: optional list of topic names.  If specified,
                converts them to use the same ids as topic names.

        Returns:
            Nothing -- modifies course in place.
        """
        def to_id(name):
            return TestCohorts.topic_name_to_id(course, name)

        topics = dict((name, {"sort_key": "A",
                              "id": to_id(name)})
                      for name in discussions)

        course.metadata["discussion_topics"] = topics

        d = {"cohorted": cohorted}
        if cohorted_discussions is not None:
            d["cohorted_discussions"] = [to_id(name)
                                         for name in cohorted_discussions]
        course.metadata["cohort_config"] = d


    def setUp(self):
        """
        Make sure that course is reloaded every time--clear out the modulestore.
        """
        # don't like this, but don't know a better way to undo all changes made
        # to course.  We don't have a course.clone() method.
        _MODULESTORES.clear()


    def test_get_cohort(self):
        # Need to fix this, but after we're testing on staging.  (Looks like
        # problem is that when get_cohort internally tries to look up the
        # course.id, it fails, even though we loaded it through the modulestore.

        # Proper fix: give all tests a standard modulestore that uses the test
        # dir.
        course = modulestore().get_course("edX/toy/2012_Fall")
        self.assertEqual(course.id, "edX/toy/2012_Fall")
        self.assertFalse(course.is_cohorted)

        user = User.objects.create(username="test", email="a@b.com")
        other_user = User.objects.create(username="test2", email="a2@b.com")

        self.assertIsNone(get_cohort(user, course.id), "No cohort created yet")

        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                               group_type=CourseUserGroup.COHORT)

        cohort.users.add(user)

        self.assertIsNone(get_cohort(user, course.id),
                          "Course isn't cohorted, so shouldn't have a cohort")

        # Make the course cohorted...
        self.config_course_cohorts(course, [], cohorted=True)

        self.assertEquals(get_cohort(user, course.id).id, cohort.id,
                          "Should find the right cohort")

        self.assertEquals(get_cohort(other_user, course.id), None,
                          "other_user shouldn't have a cohort")


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


    def test_is_commentable_cohorted(self):
        course = modulestore().get_course("edX/toy/2012_Fall")
        self.assertFalse(course.is_cohorted)

        def to_id(name):
            return self.topic_name_to_id(course, name)

        # no topics
        self.assertFalse(is_commentable_cohorted(course.id, to_id("General")),
                         "Course doesn't even have a 'General' topic")

        # not cohorted
        self.config_course_cohorts(course, ["General", "Feedback"],
                                   cohorted=False)

        self.assertFalse(is_commentable_cohorted(course.id, to_id("General")),
                         "Course isn't cohorted")

        # cohorted, but top level topics aren't
        self.config_course_cohorts(course, ["General", "Feedback"],
                                   cohorted=True)

        self.assertTrue(course.is_cohorted)
        self.assertFalse(is_commentable_cohorted(course.id, to_id("General")),
                         "Course is cohorted, but 'General' isn't.")

        self.assertTrue(
            is_commentable_cohorted(course.id, to_id("random")),
            "Non-top-level discussion is always cohorted in cohorted courses.")

        # cohorted, including "Feedback" top-level topics aren't
        self.config_course_cohorts(course, ["General", "Feedback"],
                                   cohorted=True,
                                   cohorted_discussions=["Feedback"])

        self.assertTrue(course.is_cohorted)
        self.assertFalse(is_commentable_cohorted(course.id, to_id("General")),
                         "Course is cohorted, but 'General' isn't.")

        self.assertTrue(
            is_commentable_cohorted(course.id, to_id("Feedback")),
            "Feedback was listed as cohorted.  Should be.")



