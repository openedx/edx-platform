"""
Celery needs to be loaded when the cms modules are so that task
registration and discovery can work correctly.
"""
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import APP as CELERY_APP
