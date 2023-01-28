from django import forms

class FxProgramsForm(forms.Form):
    name = forms.CharField(required=True)
    program_id = forms.CharField(required=True)
    courses_list = forms.JSONField()