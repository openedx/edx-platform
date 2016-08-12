import datetime
import logging

from django.core.management.base import BaseCommand

from student.models import CourseAccessRole
from django.contrib.auth.models import Group

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Repair users that are assistants and observers on every course
example:
    manage.py repair_users_roles_on_all_courses dryrun --settings={aws, devstack}

Options:
    createlog
                don't print all the effects but create log file
    dryrun
                do the dry run for the fixes
    repair
                repair all roles
"""

    def handle(self, *args, **options):
        if len(args) < 1 or len(args) > 2:
            print Command.help
            return

        dry_run = True
        create_log = False

        msg_string = "Script started on {}".format(datetime.datetime.now().ctime())

        if "repair" in args:
            dry_run = False
        if "dryrun" in args:
            dry_run = True
        if "createlog" in args:
            create_log = True
            fh = logging.FileHandler('repair_users_roles_on_all_courses.log')
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            log.addHandler(fh)

        log.info(msg_string)

        if dry_run:
            msg_string = "Script started in dry run mode, this will find all student roles that are conflicting on same course."
        else:
            msg_string = "Script started in repair mode, this will permanently change student role. THIS IS IRREVERSIBLE!"

        log.info(msg_string)

        all_user_roles = CourseAccessRole.objects.all()
        user_course_roles = {}

        for role_entry in all_user_roles:
            user_id = role_entry.user.id
            current_user_roles = user_course_roles.get(user_id, None)
            if current_user_roles is None:
                user_course_roles[user_id] = {}
                user_course_roles[user_id]["user_object"] = role_entry.user
                user_course_roles[user_id]["user_conflicted"] = False
                user_course_roles[user_id]["assistant_count"] = 0
                user_course_roles[user_id]["observer_count"] = 0
                user_course_roles[user_id][role_entry.course_id] = []
                user_course_roles[user_id][role_entry.course_id].append(role_entry.role)
                if role_entry.role == "assistant":
                    user_course_roles[user_id]["assistant_count"] += 1
                elif role_entry.role == "observer":
                    user_course_roles[user_id]["observer_count"] += 1
            else:
                course_data = user_course_roles[user_id].get(role_entry.course_id, None)
                if role_entry.role == "assistant":
                    user_course_roles[user_id]["assistant_count"] += 1
                elif role_entry.role == "observer":
                    user_course_roles[user_id]["observer_count"] += 1
                if course_data is None:
                    user_course_roles[user_id][role_entry.course_id] = []
                    user_course_roles[user_id][role_entry.course_id].append(role_entry.role)
                else:
                    if role_entry.role not in user_course_roles[user_id][role_entry.course_id]:
                        user_course_roles[user_id][role_entry.course_id].append(role_entry.role)
                        if "observer" in user_course_roles[user_id][role_entry.course_id] and "assistant" in user_course_roles[user_id][role_entry.course_id]:
                            if dry_run:
                                msg_string = "user id: {}, course id: {}, roles: {}".format(user_id, role_entry.course_id, user_course_roles[user_id][role_entry.course_id])
                                log.info(msg_string)
                            else:
                                role_to_delete = CourseAccessRole.objects.get(user=role_entry.user, role="observer", course_id=role_entry.course_id)
                                role_to_delete.delete()
                                user_course_roles[user_id][role_entry.course_id].remove("observer")
                            user_course_roles[user_id]["observer_count"] -= 1
                            user_course_roles[user_id]["user_conflicted"] = True

        try:
            mcka_observer_group = Group.objects.get(name__icontains="mcka_role_mcka_observer")
        except ObjectDoesNotExist:
            mcka_observer_group = None
        try:
            client_observer_group = Group.objects.get(name__icontains="mcka_role_client_observer")
        except ObjectDoesNotExist:
            client_observer_group = None

        number_of_conflicted_users = 0
        number_of_single_conflicted_users = 0

        for user_id, user_record in user_course_roles.iteritems():
            if user_record["observer_count"] == 0 and user_record["user_conflicted"]:
                if dry_run:
                    msg_string = "For user id {} this was only observer role and he should be removed from global observer groups".format(user_id)
                    log.info(msg_string)
                else:
                    if mcka_observer_group is not None:
                        user_record["user_object"].groups.remove(mcka_observer_group)
                    if client_observer_group is not None:
                        user_record["user_object"].groups.remove(client_observer_group)
                number_of_single_conflicted_users += 1
            if user_record["user_conflicted"]:
                number_of_conflicted_users += 1

        msg_string = "Fetched {} users with roles!".format(len(user_course_roles))
        msg_string += "Number of users with both observer and ta status in same course: {}, number of users that should be removed from global observer group: {}.".format(number_of_conflicted_users, number_of_single_conflicted_users)
        if not dry_run:
            log.info("All users roles are cleaned!")

        log.info(msg_string)
        log.info('--------------------------------------------------------------------------------------------------------------------')

        if create_log:
            print "Script started in create log mode, please open repair_users_roles_on_all_courses.log file."
