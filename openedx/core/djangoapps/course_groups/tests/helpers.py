"""
Helper methods for testing cohorts.
"""
import factory
from factory import post_generation, Sequence
from factory.django import DjangoModelFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum

from ..models import CourseUserGroup, CourseCohort


class CohortFactory(DjangoModelFactory):
    """
    Factory for constructing mock cohorts.
    """
    FACTORY_FOR = CourseUserGroup

    name = Sequence("cohort{}".format)
    course_id = SlashSeparatedCourseKey("dummy", "dummy", "dummy")
    group_type = CourseUserGroup.COHORT

    @post_generation
    def users(self, create, extracted, **kwargs):  # pylint: disable=unused-argument
        """
        Returns the users associated with the cohort.
        """
        if extracted:
            self.users.add(*extracted)


class CourseCohortFactory(DjangoModelFactory):
    """
    Factory for constructing mock course cohort.
    """
    FACTORY_FOR = CourseCohort

    course_user_group = factory.SubFactory(CohortFactory)
    assignment_type = 'manual'


def topic_name_to_id(course, name):
    """
    Given a discussion topic name, return an id for that name (includes
    course and url_name).
    """
    return "{course}_{run}_{name}".format(
        course=course.location.course,
        run=course.url_name,
        name=name
    )


def config_course_cohorts(
        course,
        discussions,
        cohorted,
        cohorted_discussions=None,
        auto_cohort_groups=None,
        always_cohort_inline_discussions=None  # pylint: disable=invalid-name
):
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
        auto_cohort_groups: optional list of strings
                  (names of groups to put students into).

    Returns:
        Nothing -- modifies course in place.
    """
    def to_id(name):
        return topic_name_to_id(course, name)

    topics = dict((name, {"sort_key": "A",
                          "id": to_id(name)})
                  for name in discussions)

    course.discussion_topics = topics

    config = {"cohorted": cohorted}
    if cohorted_discussions is not None:
        config["cohorted_discussions"] = [to_id(name)
                                          for name in cohorted_discussions]

    if auto_cohort_groups is not None:
        config["auto_cohort_groups"] = auto_cohort_groups

    if always_cohort_inline_discussions is not None:
        config["always_cohort_inline_discussions"] = always_cohort_inline_discussions

    course.cohort_config = config

    try:
        # Not implemented for XMLModulestore, which is used by test_cohorts.
        modulestore().update_item(course, ModuleStoreEnum.UserID.test)
    except NotImplementedError:
        pass
