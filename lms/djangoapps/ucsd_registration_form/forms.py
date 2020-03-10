from .models import UCSDCustomRegistration
from django.forms import ModelForm


class UCSDCustomRegistrationForm(ModelForm):
    """
    The fields on this form are derived from the UCSDCustomRegistration model in models.py.
    """
    def __init__(self, *args, **kwargs):
        super(UCSDCustomRegistrationForm, self).__init__(*args, **kwargs)
        # Customize error messages
        # self.fields['favorite_movie'].error_messages = {
        #    "required": u"Please tell us your favorite movie.",
        #    "invalid": u"We're pretty sure you made that movie up.",
        #}

    class Meta(object):
        model = UCSDCustomRegistration
        fields = ('gender_nb', 'ethnicity', 'age', 'education', 'howheard')
