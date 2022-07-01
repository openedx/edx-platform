from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes  # lint-amnesty, pylint: disable=wrong-import-order
from openedx.features.funix_goal.models import LearnGoal
from django.contrib.auth import get_user_model
from django.http.response import Http404


User = get_user_model()

@api_view(['POST'])
@authentication_classes((JwtAuthentication,))
@permission_classes((IsAuthenticated,))
def set_goal(request):
	def _get_student(request, target_user_id):
		if target_user_id is None:
			return request.user
		try:
			return User.objects.get(id=target_user_id)
		except User.DoesNotExist as exc:
			raise Http404 from exc

	course_id = request.data.get('course_id')
	hours_per_day = float(request.data.get('hours_per_day'))
	week_days = list(request.data.get('week_days'))
	target_user_id = request.data.get('target_user_id')

	target_user_id = int(target_user_id) if target_user_id is not None else None

	LearnGoal.set_goal(course_id=course_id, user=_get_student(request, target_user_id), hours_per_day=hours_per_day, week_days=week_days)

	return Response(status=202)
