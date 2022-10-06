import logging
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus.models import School, Class

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_schools(self, class_type, school_ids):
    schools = School.objects.filter(guid__in=school_ids)
    rm_unify = RmUnify()
    rm_unify.fetch_classes(class_type, queryset=schools)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_student(self, class_ids):
    queryset = Class.objects.filter(id__in=class_ids)
    rm_unify = RmUnify()
    rm_unify.fetch_students(query=queryset)
