import django.test
from django.contrib.auth.models import User
from django.conf import settings

from django.test.utils import override_settings

from course_groups.models import CourseUserGroup
from course_groups.cohorts import (add_cohort, get_cohort, get_course_cohorts, add_user_to_cohort,
                                   is_commentable_cohorted, get_cohort_by_name, get_cohort_by_id,
                                   get_course_cohort_names)

from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xmodule.modulestore.tests.django_utils import mixed_store_config

# NOTE: running this with the lms.envs.test config works without
# manually overriding the modulestore.  However, running with
# cms.envs.test doesn't.

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_MAPPING = {'edX/toy/2012_Fall': 'xml'}
TEST_DATA_MIXED_MODULESTORE = mixed_store_config(TEST_DATA_DIR, TEST_MAPPING)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
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
                              cohorted,
                              cohorted_discussions=None,
                              auto_cohort=None,
                              auto_cohort_groups=None):
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
            auto_cohort: optional bool.
            auto_cohort_groups: optional list of strings
                      (names of groups to put students into).

        Returns:
            Nothing -- modifies course in place.
        """
        def to_id(name):
            return TestCohorts.topic_name_to_id(course, name)

        topics = dict((name, {"sort_key": "A",
                              "id": to_id(name)})
                      for name in discussions)

        course.discussion_topics = topics

        d = {"cohorted": cohorted}
        if cohorted_discussions is not None:
            d["cohorted_discussions"] = [to_id(name)
                                         for name in cohorted_discussions]

        if auto_cohort is not None:
            d["auto_cohort"] = auto_cohort
        if auto_cohort_groups is not None:
            d["auto_cohort_groups"] = auto_cohort_groups

        course.cohort_config = d

    def setUp(self):
        """
        Make sure that course is reloaded every time--clear out the modulestore.
        """
        clear_existing_modulestores()
        self.toy_course_key = SlashSeparatedCourseKey("edX", "toy", "2012_Fall")

    def test_get_cohort(self):
        """
        Make sure get_cohort() does the right thing when the course is cohorted
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertEqual(course.id, self.toy_course_key)
        self.assertFalse(course.is_cohorted)

        user = User.objects.create(username="test", email="a@b.com")
        other_user = User.objects.create(username="test2", email="a2@b.com")

        self.assertIsNone(get_cohort(user, course.id), "No cohort created yet")

        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                                                group_type=CourseUserGroup.COHORT)

        # we shouldn't be able to create a cohort of the same name
        with self.assertRaises(ValueError):
            add_cohort(course.id, 'TestCohort')

        cohort.users.add(user)

        self.assertIsNone(get_cohort(user, course.id),
                          "Course isn't cohorted, so shouldn't have a cohort")

        # Make the course cohorted...
        self.config_course_cohorts(course, [], cohorted=True)

        self.assertEquals(get_cohort(user, course.id).id, cohort.id,
                          "Should find the right cohort")

        self.assertEquals(get_cohort(other_user, course.id), None,
                          "other_user shouldn't have a cohort")

    def test_auto_cohorting(self):
        """
        Make sure get_cohort() does the right thing when the course is auto_cohorted
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(course.is_cohorted)

        user1 = User.objects.create(username="test", email="a@b.com")
        user2 = User.objects.create(username="test2", email="a2@b.com")
        user3 = User.objects.create(username="test3", email="a3@b.com")

        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                                                group_type=CourseUserGroup.COHORT)

        # user1 manually added to a cohort
        cohort.users.add(user1)

        # Make the course auto cohorted...
        self.config_course_cohorts(course, [], cohorted=True,
                                   auto_cohort=True,
                                   auto_cohort_groups=["AutoGroup"])

        self.assertEquals(get_cohort(user1, course.id).id, cohort.id,
                          "user1 should stay put")

        self.assertEquals(get_cohort(user2, course.id).name, "AutoGroup",
                          "user2 should be auto-cohorted")

        # Now make the group list empty
        self.config_course_cohorts(course, [], cohorted=True,
                                   auto_cohort=True,
                                   auto_cohort_groups=[])

        self.assertEquals(get_cohort(user3, course.id), None,
                          "No groups->no auto-cohorting")

        # Now make it different
        self.config_course_cohorts(course, [], cohorted=True,
                                   auto_cohort=True,
                                   auto_cohort_groups=["OtherGroup"])

        self.assertEquals(get_cohort(user3, course.id).name, "OtherGroup",
                          "New list->new group")
        self.assertEquals(get_cohort(user2, course.id).name, "AutoGroup",
                          "user2 should still be in originally placed cohort")

    def test_auto_cohorting_randomization(self):
        """
        Make sure get_cohort() randomizes properly.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(course.is_cohorted)

        groups = ["group_{0}".format(n) for n in range(5)]
        self.config_course_cohorts(course, [], cohorted=True,
                                   auto_cohort=True,
                                   auto_cohort_groups=groups)

        # Assign 100 users to cohorts
        for i in range(100):
            user = User.objects.create(username="test_{0}".format(i),
                                       email="a@b{0}.com".format(i))
            get_cohort(user, course.id)

        # Now make sure that the assignment was at least vaguely random:
        # each cohort should have at least 1, and fewer than 50 students.
        # (with 5 groups, probability of 0 users in any group is about
        # .8**100= 2.0e-10)
        for cohort_name in groups:
            cohort = get_cohort_by_name(course.id, cohort_name)
            num_users = cohort.users.count()
            self.assertGreater(num_users, 1)
            self.assertLess(num_users, 50)

    def test_get_course_cohorts(self):
        course1_key = SlashSeparatedCourseKey('a', 'b', 'c')
        course2_key = SlashSeparatedCourseKey('e', 'f', 'g')

        # add some cohorts to course 1
        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course1_key,
                                                group_type=CourseUserGroup.COHORT)

        cohort = CourseUserGroup.objects.create(name="TestCohort2",
                                                course_id=course1_key,
                                                group_type=CourseUserGroup.COHORT)

        # second course should have no cohorts
        self.assertEqual(get_course_cohorts(course2_key), [])

        cohorts = sorted([c.name for c in get_course_cohorts(course1_key)])
        self.assertEqual(cohorts, ['TestCohort', 'TestCohort2'])

    def test_is_commentable_cohorted(self):
        course = modulestore().get_course(self.toy_course_key)
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

    def test_cohort_workgroup(self):
        """
        Test workgroup cohorts.
        """

        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(course.is_cohorted)

        user = User.objects.create(username="test", email="a@b.com")

        # Create cohorts
        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                                                group_type=CourseUserGroup.COHORT)
        cohort.users.add(user)

        cohort2 = CourseUserGroup.objects.create(name="TestCohort2",
                                                 course_id=course.id,
                                                 group_type=CourseUserGroup.COHORT)

        # Make the course cohorted...
        self.config_course_cohorts(course, [], cohorted=True)

        # we should be able to create a workgroup cohort of the same group
        workgroup_cohort = add_cohort(course.id, "TestCohort", group_type=CourseUserGroup.WORKGROUP)

        # add the user to a workgroup_cohort
        (_, previous_cohort) = add_user_to_cohort(workgroup_cohort,
                                                  user.username,
                                                  CourseUserGroup.WORKGROUP,
                                                  allow_multiple=True)
        self.assertIsNone(previous_cohort)

        # normal get_cohort
        self.assertEquals(cohort, get_cohort(user, course.id))
        # get workgroup_cohort
        self.assertEquals(
            workgroup_cohort,
            get_cohort(user, course.id, group_type=CourseUserGroup.WORKGROUP)
        )

        # get_cohorts tests
        self.assertEquals(
            len(get_cohort(user, course.id,
                           group_type=CourseUserGroup.WORKGROUP,
                           allow_multiple=True)),
            1
        )
        self.assertEquals(
            len(get_cohort(user, course.id, group_type=CourseUserGroup.ANY, allow_multiple=True)),
            2
        )
        self.assertEquals(
            len(get_course_cohorts(course.id, group_type=CourseUserGroup.COHORT)),
            2
        )
        self.assertEquals(
            len(get_course_cohorts(course.id, group_type=CourseUserGroup.ANY)),
            3
        )

        # shouldn't be able a cohort by name, without specifying the group_type
        with self.assertRaises(ValueError):
            get_cohort_by_name(course.id, "TestCohort", CourseUserGroup.ANY)

        self.assertEquals(
            workgroup_cohort,
            get_cohort_by_name(course.id, "TestCohort", CourseUserGroup.WORKGROUP)
        )

        # no group_type have to be specified for a get_cohort_by_id
        self.assertEquals(
            workgroup_cohort,
            get_cohort_by_id(course.id, workgroup_cohort.id)
        )

        # get_course_cohort_names tests
        self.assertEquals(
            len(get_course_cohort_names(course.id, group_type=CourseUserGroup.COHORT)),
            2
        )
        self.assertEquals(
            len(get_course_cohort_names(course.id, group_type=CourseUserGroup.ANY)),
            3
        )
        self.assertEquals(
            len(get_course_cohort_names(course.id, group_type=CourseUserGroup.WORKGROUP)),
            1
        )
