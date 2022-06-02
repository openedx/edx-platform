from django.forms import ModelForm

from openedx.features.genz_features.models import GenzUser


class GenUserRegistrationForm(ModelForm):
    """
    The fields on this form are derived from the GenzUser model in models.py.
    """

    class Meta(object):
        model = GenzUser
        fields = ('user_role', 'organisation_id', 'organisation_name', 'year_of_entry', 'registration_group', 'teacher_id')
