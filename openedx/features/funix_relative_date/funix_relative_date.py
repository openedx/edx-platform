from lms.djangoapps.courseware.courses import funix_get_assginment_date_blocks, get_course_with_access
from common.djangoapps.student.models import get_user_by_username_or_email
from openedx.features.funix_relative_date.models import FunixRelativeDateDAO
from opaque_keys.edx.keys import CourseKey

class FunixRelativeDateLibary():
	@classmethod
	def _get_last_complete_assignment(self, assignment_blocks):
		return next((asm for asm in assignment_blocks[::-1] if asm.complete), None)


	@classmethod
	def get_schedule(self, user_name, course_id):
		user = get_user_by_username_or_email(user_name)
		course_key = CourseKey.from_string(course_id)
		course = get_course_with_access(user, 'load', course_key=course_key, check_if_enrolled=False)
		assignment_blocks = funix_get_assginment_date_blocks(course=course, user=user, request=None, include_past_dates=True)

		last_complete = self._get_last_complete_assignment(assignment_blocks=assignment_blocks)

		last_complete_date = FunixRelativeDateDAO.get_enroll_by_id(user_id=user.id, course_id=course_id).date
		if last_complete is not None:
			last_complete_date = last_complete.complete_date
