import logging

from celery import shared_task

log = logging.getLogger(__name__)

@shared_task
def get_v1_libraries(request):
    print("***** in celery task get_v1_libraries ******")
