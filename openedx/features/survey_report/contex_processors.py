from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta #for months test
from .models import SurveyReport 

def admin_extra_context(request):
    months = 1
    try:
        latest_report = SurveyReport.objects.latest('created_at')
        months_treshhold = datetime.today().date() - relativedelta(months=months)  # Calculate date one month ago
        show_message = latest_report.created_at.date() <= months_treshhold
    except SurveyReport.DoesNotExist:
        show_message = False 

    return {
        'show_message': show_message,
    }