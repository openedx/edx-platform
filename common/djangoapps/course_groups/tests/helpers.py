"""
Helper methods for testing cohorts.
"""
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


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
        return topic_name_to_id(course, name)

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

    try:
        # Not implemented for XMLModulestore, which is used by test_cohorts.
        modulestore().update_item(course, ModuleStoreEnum.UserID.test)
    except NotImplementedError:
        pass
