from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_by_id
from courseware.grades import grade
from django.contrib.auth.models import User
from instructor.utils import DummyRequest

class Command(BaseCommand):

	def handle(self, *args, **options):
		import ipdb; ipdb.set_trace()
		course_id = args[0]
		course_key = CourseKey.from_string(course_id)
		course = get_course_by_id(course_key)
		request = DummyRequest()
		request.user = User.objects.get(username="staff")

		# print "grading {} students".format(User.objects.count())
		for index, user in enumerate(User.objects.all()):
			grade(user, request, course)
