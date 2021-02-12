"""
Signals for the student_certificate application.
"""
from django.dispatch import Signal

# Signal to send email to user when certificate is downloadable
USER_CERTIFICATE_DOWNLOADABLE = Signal(
    providing_args=['first_name', 'display_name', 'certificate_reverse_url', 'user_email'])
