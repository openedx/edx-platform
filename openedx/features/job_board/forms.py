
from django.forms import CharField, ModelForm, RadioSelect, TextInput

from openedx.features.job_board.models import Job


class JobCreationForm(ModelForm):
    """
    Form to handle job creation.
    """

    def __init__(self, *args, **kwargs):
        super(JobCreationForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Job
        fields = '__all__'
        widgets = {
            'type': RadioSelect,
            'compensation': RadioSelect,
            'hours': RadioSelect,
        }
        labels = {
            'company': 'Organization Name',
            'city': 'City',
            'country': 'Country',
            'title': 'Job Title',
            'type': 'Job Type',
            'compensation': 'Compensation',
            'hours': 'Job Hours',
            'description': 'Job Description',
            'function': 'Job Function',
            'responsibilities': 'Job Responsibilities',
            'website_link': 'WEBSITE LINK',
            'application_link': 'APPLICATION LINK',
            'contact_email': 'CONTACT EMAIL',
            'logo': 'Company Logo',
        }
