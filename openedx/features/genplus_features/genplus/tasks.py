import logging
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus.models import School, Class
from .constants import SchoolTypes, ClassTypes
from .xporter import Xporter

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_schools(self, class_type, school_ids):
    schools = School.objects.filter(guid__in=school_ids)
    for school in schools:
        if school.type == SchoolTypes.RM_UNIFY:
            RmUnify().fetch_classes(class_type, queryset=schools)
        elif school.type == SchoolTypes.XPORTER:
            class_type = (
                ClassTypes.XPORTER_REGISTRATION_GROUP
                if class_type == ClassTypes.REGISTRATION_GROUP
                else ClassTypes.XPORTER_TEACHING_GROUP
            )
            Xporter(school.guid).fetch_classes(class_type)

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_student(self, class_ids):
    classes = Class.objects.filter(id__in=class_ids)
    for gen_class in classes:
        if gen_class.school.type == SchoolTypes.RM_UNIFY:
            rm_unify = RmUnify()
            rm_unify.fetch_students(query=Class.objects.filter(id__in=[gen_class.id,]))
        elif gen_class.school.type == SchoolTypes.XPORTER:
            Xporter(gen_class.school.guid).fetch_students(gen_class.id)
