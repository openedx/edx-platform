from django import forms

class UploadFileForm(forms.Form):
    email = forms.EmailField(required=True)
    course_id = forms.CharField(required=True)
    block_id = forms.CharField(required=True)
    type = forms.CharField(required=True)
    file = forms.FileField(required=True)