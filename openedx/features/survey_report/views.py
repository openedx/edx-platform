"""
Views to manage the Survey Reports.
"""


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from common.djangoapps.util.views import ensure_valid_course_key
from .tasks import generate_survey_report
from .api import generate_report

class SurveyReportView(View):
    """
    View for Survey Reports.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(ensure_valid_course_key)
    def post(self, request):
        """
        Generate a new survey report using the generate_report method in api.py
        Arguments:
            request: HTTP request
        """
        survey_report_id = generate_report(defaults=True)
        generate_survey_report.delay(survey_report_id)
        return redirect("admin:survey_report_surveyreport_changelist")
