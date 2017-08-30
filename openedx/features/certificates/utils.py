"""
Functions that encapsulate business logic about the
generation and viewing of certificates and certificate fields.
"""
from config.waffle import auto_generated_certificates_enabled


def can_generate_certificate(student, course):
    if auto_generated_certificates_enabled():
        # do one thing
        pass
    else:
        # do another thing
        pass


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
        # do one thing
        pass
    else:
        # do another thing
        pass


def certificate_display_date(student, course):
    if auto_generated_certificates_enabled():
        # do one thing
        pass
    else:
        # do another thing
        pass
