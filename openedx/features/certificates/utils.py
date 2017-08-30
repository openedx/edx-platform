"""
Functions that encapsulate business logic about the
generation and viewing of certificates and certificate fields.
"""
from datetime import datetime

from config.waffle import auto_generated_certificates_enabled


def can_show_generate_certificate_button(student, course):
    if auto_generated_certificates_enabled():
        # do one thing
        pass
    else:
        # do another thing
        pass


def can_show_view_certificate_button(student, course):
    if auto_generated_certificates_enabled():
        # do one thing
        pass
    else:
        # do another thing
        pass


def can_show_course_certificate_in_program(student, course):
    if auto_generated_certificates_enabled():
        # do one thing
        pass
    else:
        # do another thing
        pass


def can_show_certificate_available_date_field(course):
    if auto_generated_certificates_enabled():
        return not course.self_paced
    return False


def certificate_display_date(course, generated_certificate):
    if auto_generated_certificates_enabled():
        if course.self_paced:
            return generated_certificate.modified_date
        else:
            available_date = course.certificate_available_date
            if (not available_date) or (available_date > datetime.utcnow()):
                return generated_certificate.modified_date
            return available_date
    else:
        return generated_certificate.modified_date
