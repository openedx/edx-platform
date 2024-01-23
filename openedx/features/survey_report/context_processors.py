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
    if not settings.ENABLE_SURVEY_REPORT:
        return {'show_survey_report_banner': False, }

    if not request.path.startswith(reverse('admin:index')):
        return {'show_survey_report_banner': False, }

    show_survey_report_banner = False
    months = settings.SURVEY_REPORT_CHECK_THRESHOLD

    try:
        latest_report = SurveyReport.objects.latest('created_at')
        months_threshold = datetime.today().date() - relativedelta(months=months)  # Calculate date one month ago
        if latest_report.created_at.date() <= months_threshold:
            show_survey_report_banner = True
    except SurveyReport.DoesNotExist:
        show_survey_report_banner = True

    return {'show_survey_report_banner': show_survey_report_banner, }
