"""
Django forms for accounts
"""


from django import forms
from django.core.exceptions import ValidationError

from openedx.core.djangoapps.user_authn.utils import generate_password


class RetirementQueueDeletionForm(forms.Form):
    """
    Admin form to facilitate learner retirement cancellation
    """
    cancel_retirement = forms.BooleanField(required=True)

    def save(self, retirement):
        """
        When the form is POSTed we double-check the retirment status
        and perform the necessary steps to cancel the retirement
        request.
        """
        if retirement.current_state.state_name != 'PENDING':
            self.add_error(
                None,
                # Translators: 'current_state' is a string from an enumerated list indicating the learner's retirement
                # state. Example: FORUMS_COMPLETE
                u"Retirement requests can only be cancelled for users in the PENDING state."
                u" Current request state for '{original_username}': {current_state}".format(
                    original_username=retirement.original_username,
                    current_state=retirement.current_state.state_name
                )
            )
            raise ValidationError('Retirement is in the wrong state!')

        # Load the user record using the retired email address -and- change the email address back.
        retirement.user.email = retirement.original_email
        # Reset users password so they can request a password reset and log in again.
        retirement.user.set_password(generate_password(length=25))
        retirement.user.save()

        # Delete the user retirement status record.
        # No need to delete the accompanying "permanent" retirement request record - it gets done via Django signal.
        retirement.delete()
