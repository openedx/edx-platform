"""
Helper methods for testing cohorts.
"""

from factory import post_generation, Sequence
from factory.django import DjangoModelFactory
import json

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum

from ..cohorts import set_course_cohort_settings
from ..models import CourseUserGroup, CourseCohort, CourseCohortsSettings, CohortMembership


class CohortFactory(DjangoModelFactory):
    """
    Factory for constructing mock cohorts.
    """
    class Meta(object):
        model = CourseUserGroup

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
            for user in self.users.all():
                CohortMembership.objects.create(
                    user=user,
                    course_user_group=self,
                )


class CourseCohortFactory(DjangoModelFactory):
    """
    Factory for constructing mock course cohort.
    """
    class Meta(object):
        model = CourseCohort


class CourseCohortSettingsFactory(DjangoModelFactory):
    """
    Factory for constructing mock course cohort settings.
    """
    class Meta(object):
        model = CourseCohortsSettings

    is_cohorted = False
    course_id = SlashSeparatedCourseKey("dummy", "dummy", "dummy")
    cohorted_discussions = json.dumps([])
    # pylint: disable=invalid-name
    always_cohort_inline_discussions = True


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


def config_course_cohorts_legacy(
        course,
        discussions,
        cohorted,
        cohorted_discussions=None,
        auto_cohort_groups=None,
        always_cohort_inline_discussions=None
):
    """
    Given a course with no discussion set up, add the discussions and set
    the cohort config on the course descriptor.

    Since cohort settings are now stored in models.CourseCohortSettings,
    this is only used for testing data migration from the CourseDescriptor
    to the table.

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
        """
        Helper method to convert a discussion topic name to a database identifier
        """
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


# pylint: disable=dangerous-default-value
def config_course_cohorts(
        course,
        is_cohorted,
        auto_cohorts=[],
        manual_cohorts=[],
        discussion_topics=[],
        cohorted_discussions=[],
        always_cohort_inline_discussions=True
):
    """
    Set discussions and configure cohorts for a course.

    Arguments:
        course: CourseDescriptor
        is_cohorted (bool): Is the course cohorted?
        auto_cohorts (list): Names of auto cohorts to create.
        manual_cohorts (list): Names of manual cohorts to create.
        discussion_topics (list): Discussion topic names. Picks ids and
            sort_keys automatically.
        cohorted_discussions: Discussion topics to cohort. Converts the
            list to use the same ids as discussion topic names.
        always_cohort_inline_discussions (bool): Whether inline discussions
            should be cohorted by default.

    Returns:
        Nothing -- modifies course in place.
    """
    def to_id(name):
        """Convert name to id."""
        return topic_name_to_id(course, name)

    set_course_cohort_settings(
        course.id,
        is_cohorted=is_cohorted,
        cohorted_discussions=[to_id(name) for name in cohorted_discussions],
        always_cohort_inline_discussions=always_cohort_inline_discussions
    )

    for cohort_name in auto_cohorts:
        cohort = CohortFactory(course_id=course.id, name=cohort_name)
        CourseCohortFactory(course_user_group=cohort, assignment_type=CourseCohort.RANDOM)

    for cohort_name in manual_cohorts:
        cohort = CohortFactory(course_id=course.id, name=cohort_name)
        CourseCohortFactory(course_user_group=cohort, assignment_type=CourseCohort.MANUAL)

    course.discussion_topics = dict((name, {"sort_key": "A", "id": to_id(name)})
                                    for name in discussion_topics)
    try:
        # Not implemented for XMLModulestore, which is used by test_cohorts.
        modulestore().update_item(course, ModuleStoreEnum.UserID.test)
    except NotImplementedError:
        pass
