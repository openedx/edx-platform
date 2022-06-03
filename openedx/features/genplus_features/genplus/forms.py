from django import forms

from openedx.features.genplus_features.genplus.models import GenUser, School


class GenUserRegistrationForm(forms.ModelForm):
    """
    The fields on this form are derived from the GenUser model in models.py.
    """
    organisation_id = forms.CharField(required=False)
    organisation_name = forms.CharField(required=False)

    class Meta(object):
        model = GenUser
        fields = ('role', 'year_of_entry', 'registration_group')

    def save(self, commit=True):
        instance = super(GenUserRegistrationForm, self).save(commit=False)
        organisation_id = self.cleaned_data.get('organisation_id')
        organisation_name = self.cleaned_data.get('organisation_name')

        if organisation_id:
            school, created = School.objects.get_or_create(guid=organisation_id, name=organisation_name)
            instance.school = school

        if commit:
            instance.save()

        return instance
