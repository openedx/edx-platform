from django.core.management.base import BaseCommand

from student.models import CourseAccessRole
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
	help = """Repair users that are assistants and observers on every course
example:
	manage.py repair_users_roles_on_all_courses --settings={aws, devstack}
"""

	def handle(self, *args, **options):

		all_user_roles = CourseAccessRole.objects.all()
		user_course_roles = {}
		for role_entry in all_user_roles:
			user_id = role_entry.user
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
		for user_id, user_record in user_course_roles.iteritems():			
			if user_record["observer_count"] == 0 and user_record["user_conflicted"]:
				if mcka_observer_group is not None:
					user_record["user_object"].groups.remove(mcka_observer_group)
				if client_observer_group is not None:
					user_record["user_object"].groups.remove(client_observer_group)
			if user_record["user_conflicted"]:
				number_of_conflicted_users += 1

		print "Fetched " + str(len(user_course_roles)) + " users with roles!"
		print "Number of users with both observer and ta status in same course: " + str(number_of_conflicted_users)
		print "All users roles are cleaned!"
