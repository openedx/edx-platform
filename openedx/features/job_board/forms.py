from django.forms import ModelForm, RadioSelect

from openedx.features.job_board.models import Job


class JobCreationForm(ModelForm):
    """
    Form to handle job creation.
    """

    class Meta:
        model = Job
        fields = '__all__'
        widgets = {
            'type': RadioSelect,
            'compensation': RadioSelect,
            'hours': RadioSelect,
        }
