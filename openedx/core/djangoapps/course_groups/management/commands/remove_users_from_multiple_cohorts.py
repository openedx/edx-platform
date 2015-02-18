"""
Script for removing users with multiple cohorts of a course from cohorts
to ensure user's uniqueness for a course cohorts
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Count

from openedx.core.djangoapps.course_groups.models import CourseUserGroup


class Command(BaseCommand):
    """
    Remove users with multiple cohorts of a course from all cohorts
    """
    help = 'Remove all users from multiple cohorts (except one) of each course'

    def handle(self, *args, **options):
        """
        Execute the command
        """
        # Get entries of cohorts which have same user added multiple times for a single course
        multiple_objects_cohorts = CourseUserGroup.objects.filter(group_type=CourseUserGroup.COHORT).\
            values_list('users', 'course_id').annotate(user_count=Count('users')).filter(user_count__gt=1).\
            order_by('users')
        multiple_objects_cohorts_count = multiple_objects_cohorts.count()
        multiple_course_cohorts_users = set(multiple_objects_cohorts.values_list('users', flat=True))
        users_failed_to_cleanup = []

        for user in User.objects.filter(id__in=multiple_course_cohorts_users):
            print u"Removing user with id '{0}' from cohort groups".format(user.id)
            try:
                # remove user from only cohorts
                user.course_groups.remove(*user.course_groups.filter(group_type=CourseUserGroup.COHORT))
            except AttributeError as err:
                users_failed_to_cleanup.append(user.email)
                print u"Failed to remove user with id {0} from cohort groups, error: {1}".format(user.id, err)

        print "=" * 80
        print u"=" * 30 + u"> Cohorts summary"
        print(
            u"Total number of CourseUserGroup of type '{0}' with multiple users: {1}".format(
                CourseUserGroup.COHORT, multiple_objects_cohorts_count
            )
        )
        print(
            u"Total number of unique users with multiple course cohorts: {0}".format(
                len(multiple_course_cohorts_users)
            )
        )
        print(
            u"Users which failed on cohorts cleanup [{0}]: [{1}]".format(
                len(users_failed_to_cleanup), (', '.join(users_failed_to_cleanup))
            )
        )
        print "=" * 80
