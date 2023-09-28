"""Helper methods for monitoring of events."""
from edx_django_utils.monitoring import set_custom_attribute, set_custom_attributes_for_course_key


def monitor_import_failure(course_key, import_step, message=None, exception=None):
    """
    Helper method to add custom parameters to for import failures.
    Arguments:
        course_key: CourseKey object
        import_step (str): current step in course import
        message (str): any particular message to add
        exception: Exception object
    """
    set_custom_attribute('course_import_failure', import_step)
    set_custom_attributes_for_course_key(course_key)

    if message:
        set_custom_attribute('course_import_failure_message', message)

    if exception is not None:
        exception_module = getattr(exception, '__module__', '')
        separator = '.' if exception_module else ''
        module_and_class = f'{exception_module}{separator}{exception.__class__.__name__}'
        exc_message = str(exception)

        set_custom_attribute('course_import_failure_error_class', module_and_class)
        set_custom_attribute('course_import_failure_error_message', exc_message)
