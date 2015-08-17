from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    # Import tasks here to avoid a circular import.
    from .tasks import update_course_structure

    # Note: The countdown=0 kwarg is set to to ensure the method below does not attempt to access the course
    # before the signal emitter has finished all operations. This is also necessary to ensure all tests pass.
    update_course_structure.apply_async([unicode(course_key)], countdown=0)
