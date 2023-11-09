from django import forms

class FeedbackForm(forms.Form):
    email = forms.EmailField()
    lesson_url = forms.URLField()
    course_code = forms.CharField(required=True)
    category_id = forms.CharField()
    content = forms.CharField(required=True)
    attachment = forms.ImageField(required=False)