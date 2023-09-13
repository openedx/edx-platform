"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""

import os

from celery.signals import task_prerun
from django.dispatch import receiver
from edx_django_utils.monitoring import set_custom_attribute

# Patch the xml libs before anything else.
from openedx.core.lib.safe_lxml import defuse_xml_libs

defuse_xml_libs()


# Set the default Django settings module for the 'celery' program
# and then instantiate the Celery singleton.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.production')
from openedx.core.lib.celery import APP  # pylint: disable=wrong-import-position,unused-import


@receiver(task_prerun)
def set_code_owner_on_celery_tasks(*, task, **kwargs):
    """
    Sets the `code_owner` custom attribute on all Celery tasks, obviating the
    need for the set_code_owner_attribute task decorator.

    ...or rather, we're not yet sure whether this works, so we're setting a
    different custom attribute first.

    See https://github.com/openedx/edx-platform/issues/33179 for details.
    """
    try:
        set_custom_attribute("auto_celery_code_owner_module", task.__module__)
    except Exception as e:  # pylint: disable=broad-except
        set_custom_attribute("auto_celery_code_owner_error", repr(e))
