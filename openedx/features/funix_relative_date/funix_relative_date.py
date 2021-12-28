from datetime import timedelta, datetime, time
import pytz
from django.urls import reverse

from lms.djangoapps.courseware.courses import funix_get_assginment_date_blocks, get_course_with_access
from common.djangoapps.student.models import get_user_by_username_or_email
from openedx.features.funix_relative_date.models import FunixRelativeDate, FunixRelativeDateDAO
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.courseware.date_summary import FunixCourseStartDate, TodaysDate

class FunixRelativeDateLibary():
	@classmethod
	def _date_to_datetime(self, date):
		return pytz.utc.localize(datetime.combine(date, time(0, 0)))

	@classmethod
	def get_course_date_blocks(self, course, user, request=None):
		assignment_blocks = funix_get_assginment_date_blocks(course=course, user=user, request=request, include_past_dates=True)
		date_blocks = FunixRelativeDateDAO.get_all_block_by_id(user_id=user.id, course_id=course.id)
		date_blocks = list(date_blocks)
		date_blocks.sort(key=lambda x: x.index)

		# Add start date
		start_date = date_blocks.pop(0)
		output = [
			FunixCourseStartDate(course=course, user=user, date=self._date_to_datetime(start_date.date)),
			TodaysDate(course=course, user=user)
		]

		date_dict = {
			str(asm.block_id): asm.date
			for asm in date_blocks
		}
		for asm in assignment_blocks:
			block_key = str(asm.block_key)
			if block_key in date_dict:
				asm.date = self._date_to_datetime(date_dict[block_key])

				link = reverse('jump_to', args=[str(course.id), block_key])
				link = request.build_absolute_uri(link) if link else ''
				asm.link = link

				output.append(asm)

		return sorted(output, key=lambda b: b.date)

	@classmethod
	def get_schedule(self, user_name, course_id):
		user = get_user_by_username_or_email(user_name)
		course_key = CourseKey.from_string(course_id)
		course = get_course_with_access(user, 'load', course_key=course_key, check_if_enrolled=False)
		assignment_blocks = funix_get_assginment_date_blocks(course=course, user=user, request=None, include_past_dates=True)

		last_complete_date = FunixRelativeDateDAO.get_enroll_by_id(user_id=user.id, course_id=course_id).date

		# Delete all old date
		FunixRelativeDateDAO.delete_all_date(user_id=user.id, course_id=course_id)

		index = 0
		completed_assignments = [asm for asm in assignment_blocks if asm.complete]
		uncompleted_assignments = [asm for asm in assignment_blocks if not asm.complete]

		completed_assignments.sort(key=lambda x: x.complete_date)
		for asm in completed_assignments:
			index += 1
			last_complete_date = asm.complete_date
			FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=asm.block_key, type='block', index=index, date=last_complete_date).save()

		for asm in uncompleted_assignments:
			index += 1
			last_complete_date += timedelta(days=1)

			FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=asm.block_key, type='block', index=index, date=last_complete_date).save()
