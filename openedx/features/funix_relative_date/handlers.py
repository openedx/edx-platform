"""
FunixRelativeDate related signal handlers.
"""
from django.dispatch import receiver

from common.djangoapps.student.models import EnrollStatusChange
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE
from openedx.features.funix_relative_date.funix_relative_date import FunixRelativeDateLibary
from openedx.features.funix_relative_date.models import FunixRelativeDate
from xmodule.modulestore.django import SignalHandler  # lint-amnesty, pylint: disable=wrong-import-order


@receiver(ENROLL_STATUS_CHANGE)
def handle_user_enroll(sender, event=None, user=None, course_id=None,**kwargs):  # pylint: disable=unused-argument
	if event == EnrollStatusChange.enroll:
		# Add user enrollment
		enrollment = FunixRelativeDate(user_id=user.id, course_id=str(course_id), block_id=None, type='start', index=0)
		enrollment.save()


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):
	FunixRelativeDateLibary.re_schedule_by_course(course_id='course-v1:FUNiX+DEP302x_01-A_VN+2021_T7')
