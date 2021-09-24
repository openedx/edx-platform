"""
Mock views for ESG
"""
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from lms.djangoapps.ora_staff_grader.mock.utils import *

class InitializeView(RetrieveAPIView):
    """ Returns initial app state """


    def get(self, request):
        course_id = request.query_params['course_id']
        ora_location = request.query_params['ora_location']

        return Response({
            'courseMetadata': get_course_metadata(course_id),
            'oraMetadata': get_ora_metadata(ora_location),
            'submissions': get_submissions(ora_location)
        })
