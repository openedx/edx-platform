"""
Signal handler for enabling self-generated certificates by default
for a self-paced courses.
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler, modulestore

from certificates import api as certs_api


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    enable the self-generated certificates by default for self-paced
    courses.
    """
    course = modulestore().get_course(course_key)
    if course.self_paced and not certs_api.cert_generation_enabled(course_key):
        certs_api.set_cert_generation_enabled(course_key, True)
