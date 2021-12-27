from lms.djangoapps.courseware.courses import get_course_assignment_date_blocks, get_course_with_access
from common.djangoapps.student.models import get_user_by_username_or_email
from opaque_keys.edx.keys import CourseKey

class FunixRelativeDate():
	@classmethod
	def get_schedule(self, user_name, course_id):
		user = get_user_by_username_or_email(user_name)
		course_key = CourseKey.from_string(course_id)
		course = get_course_with_access(user, 'load', course_key=course_key, check_if_enrolled=False)

		# courses = get_course_assignment_date_blocks(course=course, user=user, request=None, include_access=True, include_past_dates=True)

		# print(courses)
