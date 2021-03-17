"""
A trivial task for health checks
"""


from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute


@shared_task
@set_code_owner_attribute
def sample_task():
    return True
