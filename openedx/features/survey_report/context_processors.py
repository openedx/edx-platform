"""
This is the survey report contex_processor modules

This is meant to determine the visibility of the survey report banner
across all admin pages in case a survey report has not been generated

"""

from datetime import datetime
from dateutil.relativedelta import relativedelta  # for months test
from .models import SurveyReport


def admin_extra_context(request):
    months = 1
    try:
        latest_report = SurveyReport.objects.latest('created_at')
        months_treshhold = datetime.today().date() - relativedelta(months=months)  # Calculate date one month ago
        show_survey_report_banner = latest_report.created_at.date() <= months_treshhold
    except SurveyReport.DoesNotExist:
        show_survey_report_banner = False

    return {
        'show_survey_report_banner': show_survey_report_banner,
    }
