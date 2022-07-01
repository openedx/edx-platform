"""
Dates Tab Views
"""

from django.http.response import Http404
from edx_django_utils import monitoring as monitoring_utils
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_goals.models import UserActivity
from openedx.features.funix_relative_date.serializers import FUNiXDatesTabSerializer
from lms.djangoapps.course_home_api.toggles import course_home_legacy_is_active
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from openedx.features.funix_relative_date.funix_relative_date import FunixRelativeDateLibary
from lms.djangoapps.courseware.date_summary import TodaysDate
from lms.djangoapps.courseware.masquerade import setup_masquerade
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.funix_goal.models import LearnGoal
from django.contrib.auth import get_user_model

User = get_user_model()

class FunixRelativeDatesTabView(RetrieveAPIView):
	authentication_classes = (
		JwtAuthentication,
		BearerAuthenticationAllowInactiveUser,
		SessionAuthenticationAllowInactiveUser,
	)
	permission_classes = (IsAuthenticated,)
	serializer_class = FUNiXDatesTabSerializer

	def _get_student_user(self, request, course_key, student_id, is_staff):
		if student_id:
			try:
				student_id = int(student_id)
			except ValueError as e:
				raise Http404 from e

		if student_id is None or student_id == request.user.id:
			_, student = setup_masquerade(
				request,
				course_key,
				staff_access=is_staff,
				reset_masquerade_data=True
			)
			return student

		try:
			return User.objects.get(id=student_id)
		except User.DoesNotExist as exc:
			raise Http404 from exc

	def get(self, request, *args, **kwargs):
		course_key_string = kwargs.get('course_key_string')
		course_key = CourseKey.from_string(course_key_string)
		student_id = kwargs.get('student_id')

		if course_home_legacy_is_active(course_key):
			raise Http404

		# Enable NR tracing for this view based on course
		monitoring_utils.set_custom_attribute('course_id', course_key_string)
		monitoring_utils.set_custom_attribute('user_id', request.user.id)
		monitoring_utils.set_custom_attribute('is_staff', request.user.is_staff)

		course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)
		is_staff = bool(has_access(request.user, 'staff', course_key))

		user_data = self._get_student_user(request, course_key, student_id, is_staff)

		if not CourseEnrollment.is_enrolled(user_data, course_key) and not is_staff:
			return Response('User not enrolled.', status=401)

		blocks = FunixRelativeDateLibary.get_course_date_blocks(course=course,user=user_data, request=request)

		learner_is_full_access = not ContentTypeGatingConfig.enabled_for_enrollment(
			user=user_data,
			course_key=course_key,
		)

		# User locale settings
		user_timezone_locale = user_timezone_locale_prefs(request)
		user_timezone = user_timezone_locale['user_timezone']

		# Get goal
		goal = LearnGoal.get_goal(course_id=course_key_string, user_id=str(user_data.id))

		data = {
			'has_ended': course.has_ended(),
			'course_date_blocks': [block for block in blocks if not isinstance(block, TodaysDate)],
			'learner_is_full_access': learner_is_full_access,
			'user_timezone': user_timezone,
			'goal_hours_per_day': goal.hours_per_day,
			'goal_weekdays': [getattr(goal, f'weekday_{i}') for i in range(7)],
			'username': user_data.username
		}
		context = self.get_serializer_context()
		context['learner_is_full_access'] = learner_is_full_access
		serializer = self.get_serializer_class()(data, context=context)

		return Response(serializer.data)
