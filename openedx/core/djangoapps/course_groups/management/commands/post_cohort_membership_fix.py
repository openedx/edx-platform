"""
Intended to fix any inconsistencies that may arise during the rollout of the CohortMembership model.
Illustration: https://gist.github.com/efischer19/d62f8ee42b7fbfbc6c9a
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from openedx.core.djangoapps.course_groups.models import CourseUserGroup, CohortMembership


class Command(BaseCommand):
    """
    Repair any inconsistencies between CourseUserGroup and CohortMembership. To be run after migration 0006.
    """
    help = '''
    Repairs any potential inconsistencies made in the window between running migrations 0005 and 0006, and deploying
    the code changes to enforce use of CohortMembership that go with said migrations.
    |commit|: optional argument. If not provided, will dry-run and list number of operations that would be made.
    '''

    def handle(self, *args, **options):
        """
        Execute the command. Since this is designed to fix any issues cause by running pre-CohortMembership code
        with the database already migrated to post-CohortMembership state, we will use the pre-CohortMembership
        table CourseUserGroup as the canonical source of truth. This way, changes made in the window are persisted.
        """
        commit = 'commit' in options
        memberships_to_delete = 0
        memberships_to_add = 0

        # Begin by removing any data in CohortMemberships that does not match CourseUserGroups data
        for membership in CohortMembership.objects.all():
            try:
                CourseUserGroup.objects.get(
                    group_type=CourseUserGroup.COHORT,
                    users__id=membership.user.id,
                    course_id=membership.course_id,
                    id=membership.course_user_group.id
                )
            except CourseUserGroup.DoesNotExist:
                memberships_to_delete += 1
                if commit:
                    membership.delete()

        # Now we can add any CourseUserGroup data that is missing a backing CohortMembership
        for course_group in CourseUserGroup.objects.filter(group_type=CourseUserGroup.COHORT):
            for user in course_group.users.all():
                try:
                    CohortMembership.objects.get(
                        user=user,
                        course_id=course_group.course_id,
                        course_user_group_id=course_group.id
                    )
                except CohortMembership.DoesNotExist:
                    memberships_to_add += 1
                    if commit:
                        membership = CohortMembership(
                            course_user_group=course_group,
                            user=user,
                            course_id=course_group.course_id
                        )
                        try:
                            membership.save()
                        except IntegrityError:  # If the user is in multiple cohorts, we arbitrarily choose between them
                            # In this case, allow the pre-existing entry to be "correct"
                            course_group.users.remove(user)
                            user.course_groups.remove(course_group)

        print '{} CohortMemberships did not match the CourseUserGroup table and will be deleted'.format(
            memberships_to_delete
        )
        print '{} CourseUserGroup users do not have a CohortMembership; one will be added if it is valid'.format(
            memberships_to_add
        )
        if commit:
            print 'Changes have been made and saved.'
        else:
            print 'Dry run, changes have not been saved. Run again with "commit" argument to save changes'
