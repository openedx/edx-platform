"""
Forms for Job Board app
"""
from django.forms import ModelForm, RadioSelect

from openedx.features.job_board.models import Job


class JobCreationForm(ModelForm):
    """
    Form to handle job creation.
    """

    class Meta:
        model = Job
        exclude = ('user',)
        fields = '__all__'
        widgets = {
            'type': RadioSelect,
            'compensation': RadioSelect,
            'hours': RadioSelect,
        }
        labels = {
            # add labels with trailing colon
            'city': 'City:',
            'country': 'Country:',
            'application_link': 'APPLICATION LINK:',
            'website_link': 'WEBSITE LINK:',
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(JobCreationForm, self).__init__(*args, **kwargs)

        initial_arguments = kwargs.get('initial', {})
        self.user = initial_arguments.get('user', None)

    def save(self):  # pylint: disable=arguments-differ
        job = super(JobCreationForm, self).save(commit=False)
        job.user = self.user
        job.save()
        return job
