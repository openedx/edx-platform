"""
FunixRelativeDate related signal handlers.
"""
from django.dispatch import receiver
from lms.djangoapps.grades.api import signals as grades_signals
from common.djangoapps.student.models import EnrollStatusChange
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE
from openedx.features.funix_relative_date.funix_relative_date import FunixRelativeDateLibary
from openedx.features.funix_relative_date.models import FunixRelativeDate
from xmodule.modulestore.django import SignalHandler  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.student.models import get_user_by_id
import asyncio


@receiver(ENROLL_STATUS_CHANGE)
def handle_user_enroll(sender, event=None, user=None, course_id=None,**kwargs):  # pylint: disable=unused-argument
	if event == EnrollStatusChange.enroll:
		# Add user enrollment
		enrollment = FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=None, type='start', index=0)
		enrollment.save()

		FunixRelativeDateLibary.get_schedule(user_name=user.username, course_id=str(course_id))

@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):
	FunixRelativeDateLibary.re_schedule_by_course(course_id=str(course_key))
# @receiver(grades_signals.PROBLEM_WEIGHTED_SCORE_CHANGED)
# def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
# 	user_id = kwargs.get('user_id', None)
# 	course_id = kwargs.get('course_id', None)

# 	user = get_user_by_id(user_id)
# 	asyncio.run(async_update_schedule(username=user.username, course_id=str(course_id)))
# 	print('--243-23554-342')



# async def async_update_schedule(username, course_id):
# 	print('lkasjdfasdasd', username, course_id)
# 	await asyncio.sleep(5)
# 	print('--done--')
# 	FunixRelativeDateLibary.get_schedule(user_name=username, course_id=course_id)
