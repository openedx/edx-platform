import json
from rest_framework import generics
from rest_framework.response import Response
from .api import get_course_blocks

from django.http import HttpResponse

from mobile_api.utils import mobile_view, mobile_course_access

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

def structure_view(request, course_id):

	try:
		course_key = CourseKey.from_string(course_id)
	except InvalidKeyError:
		course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

	return HttpResponse(
		get_course_blocks(request.user, course_key), 
		content_type="text/plain", 
		status=200
	)
