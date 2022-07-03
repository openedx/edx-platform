from datetime import timedelta, datetime, time, date
import pytz
import math
from django.urls import reverse

import  lms.djangoapps.courseware.courses as courseware_courses
from common.djangoapps.student.models import get_user_by_username_or_email, get_user_by_id
from openedx.features.funix_relative_date.models import FunixRelativeDate, FunixRelativeDateDAO
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.courseware.date_summary import FunixCourseStartDate, TodaysDate
from openedx.features.funix_goal.models import LearnGoal

class FunixRelativeDateLibary():
	TIME_PER_DAY = 2.5 * 60

	@classmethod
	def _date_to_datetime(self, date):
		return pytz.utc.localize(datetime.combine(date, time(0, 0)))

	@classmethod
	def get_course_date_blocks(self, course, user, request=None):
		assignment_blocks = courseware_courses.funix_get_assginment_date_blocks(course=course, user=user, request=request, include_past_dates=True)
		date_blocks = FunixRelativeDateDAO.get_all_block_by_id(user_id=user.id, course_id=course.id)
		date_blocks = list(date_blocks)
		date_blocks.sort(key=lambda x: x.index)

		# Check if date_blocks is empty
		if len(date_blocks) == 0:
			return []

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
		output = sorted(output, key=lambda b: b.date)

		check_complete = True
		for el in output:
			if el.css_class == 'assignment':
				if not el.complete:
					check_complete = False
				else:
					if not check_complete:
						self.get_schedule(user_name=user.username, course_id=str(course.id), assignment_blocks=assignment_blocks)
						return self.get_course_date_blocks(course=course, user=user, request=request)
		return output

	@classmethod
	def get_schedule(self, user_name, course_id, assignment_blocks=None):
		def get_time(last_complete_date, goal, day=1):
			last_complete_date += timedelta(days=day)
			weekday = last_complete_date.weekday()

			if not getattr(goal, f'weekday_{weekday}'):
				return get_time(last_complete_date, goal)

			return last_complete_date

		user = get_user_by_username_or_email(user_name)
		course_key = CourseKey.from_string(course_id)
		course = courseware_courses.get_course_with_access(user, 'load', course_key=course_key, check_if_enrolled=False)

		if assignment_blocks is None:
			assignment_blocks = courseware_courses.funix_get_assginment_date_blocks(course=course, user=user, request=None, include_past_dates=True)

		last_complete_date = FunixRelativeDateDAO.get_enroll_date_by_id(user_id=user.id, course_id=course_id)
		if last_complete_date is None:
			last_complete_date = date.today()

		# Delete all old date
		FunixRelativeDateDAO.delete_all_date(user_id=user.id, course_id=course_id)

		# Get goal
		goal = LearnGoal.get_goal(course_id=course_id, user_id=str(user.id))
		index = 0
		completed_assignments = [asm for asm in assignment_blocks if asm.complete]
		uncompleted_assignments = [asm for asm in assignment_blocks if not asm.complete]

		completed_assignments.sort(key=lambda x: x.complete_date)
		for asm in completed_assignments:
			index += 1
			last_complete_date = asm.complete_date
			FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=asm.block_key, type='block', index=index, date=last_complete_date).save()

		left_time = float(goal.hours_per_day) * 60
		arr = []
		for asm in uncompleted_assignments:
			effort_time = asm.effort_time
			if effort_time <= left_time:
				arr.append(asm)
				left_time -= effort_time
			else:
				last_complete_date = get_time(last_complete_date, goal)
				for el in arr:
					index += 1
					FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=el.block_key, type='block', index=index, date=last_complete_date).save()
				left_time = float(goal.hours_per_day) * 60
				if effort_time > left_time:
					index += 1

					day_need = math.ceil(effort_time / left_time)
					last_complete_date = get_time(last_complete_date, goal, day=day_need)
					FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=asm.block_key, type='block', index=index, date=last_complete_date).save()
					arr = []
				else:
					arr = [asm]
					left_time -= effort_time

	@classmethod
	def re_schedule_by_course(self, course_id):
		enroll_list = FunixRelativeDateDAO.get_all_enroll_by_course(course_id=course_id)
		for user_el in enroll_list:
			user = get_user_by_id(user_el.user_id)
			self.get_schedule(user_name=user.username, course_id=str(course_id))
