"""
Defines a form for providing validation of CourseEmail templates.
"""
import logging

from django import forms
from django.core.exceptions import ValidationError

from bulk_email.models import CourseEmailTemplate, COURSE_EMAIL_MESSAGE_BODY_TAG

log = logging.getLogger(__name__)


class CourseEmailTemplateForm(forms.ModelForm):
    """Form providing validation of CourseEmail templates."""

    class Meta:  # pylint: disable=C0111
        model = CourseEmailTemplate

    def _validate_template(self, template):
        """Check the template for required tags."""
        index = template.find(COURSE_EMAIL_MESSAGE_BODY_TAG)
        if index < 0:
            msg = 'Missing tag: "{}"'.format(COURSE_EMAIL_MESSAGE_BODY_TAG)
            log.warning(msg)
            raise ValidationError(msg)
        if template.find(COURSE_EMAIL_MESSAGE_BODY_TAG, index + 1) >= 0:
            msg = 'Multiple instances of tag: "{}"'.format(COURSE_EMAIL_MESSAGE_BODY_TAG)
            log.warning(msg)
            raise ValidationError(msg)
        # TODO: add more validation here, including the set of known tags
        # for which values will be supplied.  (Email will fail if the template
        # uses tags for which values are not supplied.)

    def clean_html_template(self):
        """Validate the HTML template."""
        template = self.cleaned_data["html_template"]
        self._validate_template(template)
        return template

    def clean_plain_template(self):
        """Validate the plaintext template."""
        template = self.cleaned_data["plain_template"]
        self._validate_template(template)
        return template
