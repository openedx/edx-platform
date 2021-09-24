"""
Mock views for ESG
"""
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView

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


class FetchSubmissionView(RetrieveAPIView):
    """ Get a submission """

    def get(self, request):
        submission_id = request.query_params['submissionId']

        submission = fetch_submission(submission_id)
        response = fetch_response(submission_id)

        return Response({
            'gradeData': submission['gradeData'],
            'response': response,
            'gradeStatus': submission['gradeStatus'],
        })



class FetchSubmissionStatusView(RetrieveAPIView):
    """ Get a submission status """

    def get(self, request):
        submission_id = request.query_params['submissionId']

        submission = fetch_submission(submission_id)

        return Response({
            'gradeStatus': submission['gradeStatus'],
            'lockStatus': submission['lockStatus'],
            'gradeData': submission['gradeData']
        })


class LockView(APIView):
    """ Lock a submission for grading """

    def lock_submission(self, submission, value):
        """
        Change lock status on a submission.
        For now, that means updating to "in-progress" when requested
        or to "unlocked" when a lock is released
        """
        submission['lockStatus'] = 'in-progress' if value else 'unlocked'
        return submission


    def post(self, request):
        value = request.query_params['value'] == "true"  # Bool, whether to lock (True) or unlock (False) submission
        submission_id = request.query_params['submissionId']

        submission = fetch_submission(submission_id)

        self.lock_submission(submission, value)
        save_submission_update(submission)

        return Response({
            "lockStatus": submission['lockStatus']
        })

class UpdateGradeView(RetrieveAPIView):
    """ Submit a grade """

    def update_grade_data(self, submission, grade_data):
        submission['gradeData'] = grade_data
        submission['score'] = grade_data['score']
        submission['gradeStatus'] = 'graded'
        submission['lockStatus'] = 'unlocked'

    def post(self, request):
        submission_id = request.query_params['submissionId']
        grade_data = request.data

        submission = fetch_submission(submission_id)

        self.update_grade_data(submission, grade_data)
        save_submission_update(submission)

        return Response({
            'gradeData': submission['gradeData']
        })
