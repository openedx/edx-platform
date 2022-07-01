from django import forms

class FeedbackForm(forms.Form):
    email = forms.EmailField()
    lesson_url = forms.URLField()
    unit_title = forms.CharField(required=False)
    instance_code = forms.CharField(required=False)
    category_id = forms.CharField()
    content = forms.CharField(required=True)
    attachment = forms.ImageField(required=False)