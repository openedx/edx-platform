from django.conf import settings
from django.urls import reverse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from .models import SurveyReport

def admin_extra_context(request):
    """
    This function sends extra context to every admin site.
    The current threshold to show the banner is one month but this can be redefined in the future.
    """
    if not settings.SURVEY_REPORT_ENABLE or not request.path.startswith(reverse('admin:index')):
        return {'show_survey_report_banner': False}

    return {'show_survey_report_banner': should_show_survey_report_banner()}

def should_show_survey_report_banner():
    """
    Determine whether to show the survey report banner based on the threshold.
    """
    months_threshold = get_months_threshold(settings.SURVEY_REPORT_CHECK_THRESHOLD)

    try:
        latest_report = SurveyReport.objects.latest('created_at')
        return latest_report.created_at.date() <= months_threshold
    except SurveyReport.DoesNotExist:
        return True

def get_months_threshold(months):
    """
    Calculate the date threshold based on the specified number of months.
    """
    return datetime.today().date() - relativedelta(months=months)
