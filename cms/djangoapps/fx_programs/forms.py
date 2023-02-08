from django import forms

class FxProgramsForm(forms.Form):
    name = forms.CharField(required=True)
    program_id = forms.CharField(required=True)
    course_list = forms.CharField(required=False)
    id_course_list = forms.CharField(required=False)
    metadata = forms.JSONField()