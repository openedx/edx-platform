"""
A trivial task for health checks
"""


from celery.task import task


@task
def sample_task():
    return True
