"""
A trivial task for health checks
"""


from celery.task import task
from edx_django_utils.monitoring import set_code_owner_attribute


@task
@set_code_owner_attribute
def sample_task():
    return True
