from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import MultipleObjectsReturned
from optparse import make_option

from django.contrib.auth.models import User

from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from course_groups.models import CourseUserGroup
from course_groups.cohorts import (
    get_cohort,
    get_cohort_by_name,
    add_cohort,
    add_user_to_cohort,
    remove_user_from_cohort
)
from student.models import CourseEnrollment


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--fix',
            action='store_true',
            dest='fix',
            default=False,
            help='Apply possible fixes automatically'),
    )
    help = 'Revert the multiple cohorts feature.'

    def handle(self, *args, **options):

        self.stdout.write('### Checking CourseUserGroup group types\n')
        error = False
        for course_group in CourseUserGroup.objects.all():
            if course_group.group_type != CourseUserGroup.COHORT:
                if options['fix']:
                    self.stdout.write(
                        'Fixed: CourseUserGroup with an invalid group_type found: {} (type: {})\n'.format(
                            course_group.name, course_group.group_type)
                    )
                    course_group.group_type = CourseUserGroup.COHORT
                    course_group.save()
                else:
                    error = True
                    self.stdout.write(
                        'CourseUserGroup with an invalid group_type found: {} (type: {})\n'.format(
                            course_group.name, course_group.group_type)
                    )

        if not error:
            self.stdout.write('Ok.\n')

        self.stdout.write('\n### Checking user cohorts\n')
        error = False
        users = User.objects.all()
        _courses = modulestore().get_courses()
        courses = [c for c in _courses if isinstance(c, CourseDescriptor)]
        # for each course, check if users are in atleast and only 1 cohort
        for course in courses:
            for user in users:
                if not CourseEnrollment.is_enrolled(user, course.id):
                    continue
                try:
                    CourseUserGroup.objects.get(course_id=course.id,
                                                users__id=user.id)
                except CourseUserGroup.DoesNotExist:
                    if options['fix']:
                        # create a "default_cohort" is it doesn't already exist
                        try:
                            default_cohort = get_cohort_by_name(course.id, CourseUserGroup.default_cohort_name)
                        except CourseUserGroup.DoesNotExist:
                            default_cohort = add_cohort(course.id, CourseUserGroup.default_cohort_name)
                            self.stdout.write('Default cohort "{}" created for course "{}"'.format(
                                default_cohort.name, course.display_name)
                            )
                        add_user_to_cohort(default_cohort, user.username)
                        self.stdout.write(
                            'Fixed: User "{}" is not in a cohort in course "{}". Added in "{}" cohort\n'.format(
                                user.username, course.display_name, default_cohort.name)
                        )
                    else:
                        error = True
                        self.stdout.write(
                            'User "{}" is not in a cohort in course "{}".\n'.format(
                                user.username, course.display_name)
                        )
                except MultipleObjectsReturned:
                    self.stdout.write(
                        'User "{}" is in multiple cohorts in course "{}".\n'.format(
                            user.username, course.display_name)
                    )
                    if options['fix']:
                        user_cohorts = CourseUserGroup.objects.filter(course_id=course.id,
                                                                      users__id=user.id).all()
                        user_cohort = user_cohorts[0]
                        for cohort in user_cohorts[1:]:
                            remove_user_from_cohort(cohort, user.username)
                            self.stdout.write("User '{}' has been removed from cohort '{}' in course '{}'.\n".format(
                                user.username, cohort.name, course.display_name)
                            )

                        self.stdout.write("User '{}' is now only in cohort '{}' in course '{}'.\n".format(
                            user.username, cohort.name, course.display_name)
                        )
                    else:
                        error = True

        if not error:
            self.stdout.write('Ok.\n')

        self.stdout.write('\nTo fix issues, run the script with the "--fix" option.\n')
