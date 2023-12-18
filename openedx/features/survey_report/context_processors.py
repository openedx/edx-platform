"""
This is the survey report contex_processor modules

This is meant to determine the visibility of the survey report banner
across all admin pages in case a survey report has not been generated

"""

from datetime import datetime
from dateutil.relativedelta import relativedelta  # for months test
from .models import SurveyReport
from django.urls import reverse
from django.conf import settings


def admin_extra_context(request):
    """
    This function sends extra context to every admin site

    The current treshhold to show the banner is one month but this can be redefined in the future

    """
    months = settings.SURVEY_REPORT_CHECK_THRESHOLD
    if not request.path.startswith(reverse('admin:index')):
        return {'show_survey_report_banner': False, }

    try:
        latest_report = SurveyReport.objects.latest('created_at')
        months_treshhold = datetime.today().date() - relativedelta(months=months)  # Calculate date one month ago
        show_survey_report_banner = latest_report.created_at.date() <= months_treshhold
    except SurveyReport.DoesNotExist:
        show_survey_report_banner = True

    return {'show_survey_report_banner': show_survey_report_banner, }
