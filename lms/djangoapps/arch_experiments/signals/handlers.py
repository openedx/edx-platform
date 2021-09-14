from common.djangoapps.student.signals.signals import (
    UNENROLL_DONE
)
from django.dispatch import receiver
from pprint import pprint
from django.conf import settings
import json

@receiver(UNENROLL_DONE)
def transmit_unenrollment_to_event_bus(course_enrollment, **kwargs):
    print("="*80)
    print("="*80)
    pprint(kwargs)
    print("="*80)
    print("="*80)
    enrollment_data = {
        "user_id": course_enrollment.user.id,
        "course": str(course_enrollment.course.id),
        "mode": course_enrollment.mode,
    }
    settings.ARCH_EXPERIMENTS_PRODUCER.send(
            content=json.dumps(enrollment_data).encode(),
            partition_key=str(course_enrollment.id),
        )
