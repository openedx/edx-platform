import datetime
import logging

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from student.models import CourseAccessRole
from django.contrib.auth.models import Group
from edx_solutions_api_integration.models import CourseGroupRelationship
from edx_solutions_api_integration.courseware_access import get_course_key
from courseware import courses

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '''Remove instructor role of internal admins on courses in their organization and add it on internal tagged courses
example:
    ./manage.py lms repair_internal_admin_instructor_role dryrun --settings={aws, devstack}

Options:
    createlog
                don't print all the effects but create log file
    dryrun
                do the dry run for the fixes
    repair
                repair all roles
'''

    def handle(self, *args, **options):
        if len(args) < 1 or len(args) > 2:
            print Command.help
            return

        dry_run = True
        create_log = False

        msg_string = 'Script started on {}'.format(datetime.datetime.now().ctime())

        if 'repair' in args:
            dry_run = False
        if 'dryrun' in args:
            dry_run = True
        if 'createlog' in args:
            create_log = True
            file_handler = logging.FileHandler('repair_internal_admin_instructor_role.log')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
            file_handler.setFormatter(formatter)
            log.addHandler(file_handler)

        log.info(msg_string)

        if dry_run:
            msg_string = 'Script started in dry run mode, this will print for all internal admins courses for which we need to remove or add theirs instructor role'
        else:
            msg_string = 'Script started in repair mode, this will permanently remove or add instructor role of internal admins. THIS IS IRREVERSIBLE!'

        log.info(msg_string)

        internal_admin_group_name = 'mcka_role_internal_admin'
        internal_tag_group_type = 'tag:internal'
        instructor_role = 'instructor'
        staff_role = 'staff'
        number_of_removed_roles = 0
        number_of_added_roles = 0

        #get all internal admins
        try:
            internal_admin_group = Group.objects.get(name__icontains=internal_admin_group_name)
        except ObjectDoesNotExist:
            internal_admin_group = None

        if internal_admin_group:
            internal_admins = internal_admin_group.user_set.all()

        #get internal tagged courses
        try:
            internal_courses_group = Group.objects.get(groupprofile__group_type=internal_tag_group_type)
        except ObjectDoesNotExist:
            internal_courses_group = None

        if internal_courses_group:
            internal_courses = CourseGroupRelationship.objects.filter(group=internal_courses_group)
            internal_courses_ids = []
            for internal_course in internal_courses:
                internal_courses_ids.append(internal_course.course_id)

        #for all internal admins check their roles and remove instructor role on course if he doesn't have staff role on course and course isn't tagged internal
        for internal_admin in internal_admins:
            user_roles = CourseAccessRole.objects.filter(user=internal_admin)

            instructor_courses = []
            staff_courses = []
            for user_role in user_roles:
                if user_role.role == instructor_role:
                    instructor_courses.append(user_role.course_id)
                if user_role.role == staff_role:
                    staff_courses.append(user_role.course_id)

            for instructor_course in instructor_courses:
                if str(instructor_course) not in internal_courses_ids and instructor_course not in staff_courses:
                    number_of_removed_roles += 1
                    if dry_run:
                        msg_string = 'Remove instructor role for internal admin ' + str(internal_admin.id) + ' on course ' + str(instructor_course) + '.'
                        log.info(msg_string)
                    else:
                        role_to_delete = CourseAccessRole.objects.get(user=internal_admin, role=instructor_role, course_id=instructor_course)
                        role_to_delete.delete()

        #for all internal tagged course check roles and if internal admins don't have instructor role on course add it
        for internal_course in internal_courses:
            course_id = get_course_key(internal_course.course_id)
            course_roles = CourseAccessRole.objects.filter(course_id=course_id)
            instructor_users = []
            for course_role in course_roles:
                if course_role.role == instructor_role:
                    instructor_users.append(course_role.user_id)

            for internal_admin in internal_admins:
                if internal_admin.id not in instructor_users:
                    number_of_added_roles += 1
                    if dry_run:
                        msg_string = 'Add instructor role for internal admin ' + str(internal_admin.id) + ' on course ' + str(course_id) + '.'
                        log.info(msg_string)
                    else:
                        course = courses.get_course(course_id, 0)
                        new_role = CourseAccessRole(user=internal_admin, role=instructor_role, course_id=course.id, org=course.org)
                        new_role.save()

        msg_string = 'Number of removed roles: ' + str(number_of_removed_roles) + '.'
        log.info(msg_string)
        msg_string = 'Number of added roles: ' + str(number_of_added_roles) + '.'
        log.info(msg_string)

        log.info('--------------------------------------------------------------------------------------------------------------------')

        if create_log:
            print 'Script started in create log mode, please open repair_internal_admin_instructor_role.log file.'
