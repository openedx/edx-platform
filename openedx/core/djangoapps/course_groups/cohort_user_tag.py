"""
User Tag Provider for partitioned cohorts.
"""
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.users.user_tags.contexts.course import UserTagProviderCourseContext
from openedx.core.djangoapps.users.user_tags.tag import UserTag
from openedx.core.djangoapps.course_groups.cohorts import get_course_cohorts, get_cohort


class CohortUserTag(UserTag):
    """
    UserTag class for partitioned cohorts.
    """
    def __init__(self, course_user_group):
        self._course_user_group = course_user_group

    @property
    def name(self):
        return self._course_user_group.name

    @property
    def display_name(self):
        return self.name

    @property
    def description(self):
        return _(u'Partitioned Cohort for {}').format(self.display_name)

    @property
    def course_key(self):
        """
        Returns the course key associated with this tag.
        """
        return self._course_user_group.course_id

    @property
    def users(self):
        """
        Returns the users associated with this tag.
        """
        return self._course_user_group.users.all()


class CohortUserTagProvider(UserTagProviderCourseContext):
    """
    UserTagProvider class for partitioned cohorts.
    """
    tag_type = CohortUserTag

    @classmethod
    def name(cls):
        return u'openedx.partitioned_cohorts'

    @classmethod
    def course_tags(cls, course_context=None, **kwargs):
        cohorts = get_course_cohorts(course_context.course, **kwargs)
        return [CohortUserTag(cohort) for cohort in cohorts]

    @classmethod
    def get_users_for_course_tag(cls, tag, course_context=None, **kwargs):
        return tag.users

    @classmethod
    def get_course_tags_for_user(cls, user, course_context=None, **kwargs):
        cohort = get_cohort(user, course_context.id, **kwargs)
        return [CohortUserTag(cohort)] if cohort else []
