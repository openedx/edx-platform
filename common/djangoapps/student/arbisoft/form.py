from django import forms
from student.models import (
    CandidateProfile,
    CandidateExpertise,
    CandidateReference)
from student.arbisoft import constants as arbi_constants


class CandidateProfileForm(forms.ModelForm):
    studied_course = forms.MultipleChoiceField(
        choices=arbi_constants.STUDIED_COURSES,
        required=True,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'input-inline checkbox',
            }
        ),
        label='Check mark the courses you studied'
    )
    technology = forms.MultipleChoiceField(
        choices=arbi_constants.TECHNOLOGIES,
        required=True,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'input-inline checkbox'
            }
        ),
        label="Mark the technology you'd like to work on/learn"
    )

    class Meta:
        model = CandidateProfile
        fields = (
            'graduation_date',
            'phone_number',
            'cgpa',
            'position_in_class',
            'academic_projects',
            'extra_curricular_activities',
            'freelance_work',
            'accomplishment',
            'individuality_factor',
            'ideal_organization',
            'why_arbisoft',
            'expected_salary',
            'career_plan',
            'other_studied_course',
            'other_technology',
        )
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'input-block', 'required': 'true', 'maxlength': 20}),
            'graduation_date': forms.TextInput(attrs={'class': 'date', 'type': 'text', 'required': 'true'}),
            'cgpa': forms.TextInput(attrs={'class': 'input-block', 'type': 'decimal', 'required': 'true'}),
            'position_in_class': forms.TextInput(attrs={'class': 'input-block'}),
            'academic_projects': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'extra_curricular_activities': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'maxlength': 255}
            ),
            'freelance_work': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'maxlength': 255}
            ),
            'accomplishment': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'individuality_factor': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'ideal_organization': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'why_arbisoft': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'expected_salary': forms.TextInput(attrs={'class': 'input-block', "type": "number", 'required': 'true'}),
            'career_plan': forms.Textarea(
                attrs={'class': 'input-block', "type": "textarea", "rows": 4, 'required': 'true', 'maxlength': 255}
            ),
            'other_studied_course': forms.TextInput(
                attrs={'class': 'input-block', "type": "textarea", "rows": 1, 'maxlength': 255}
            ),
            'other_technology': forms.TextInput(
                attrs={'class': 'input-block', "type": "textarea", "rows": 1, 'maxlength': 255}
            ),
        }

    def clean(self):
        cleaned_data = super(CandidateProfileForm, self).clean()
        #
        # position_in_class = cleaned_data.get('position_in_class')
        # if position_in_class < 0:
        #     self.add_error('position_in_class', forms.ValidationError("Invalid value."))
        #     raise forms.ValidationError("Invalid value.")

        cgpa = cleaned_data.get('cgpa')
        if cgpa < 0 or cgpa > 4:
            self.add_error('cgpa', forms.ValidationError("Invalid value."))
            raise forms.ValidationError("Valid range is 0 to 4")
        expected_salary = cleaned_data.get('expected_salary')

        if expected_salary < 0:
            self.add_error('expected_salary', forms.ValidationError("Invalid value."))
            raise forms.ValidationError("Invalid value.")

        return cleaned_data


class CandidateExpertiseForm(forms.ModelForm):
    class Meta:
        model = CandidateExpertise
        fields = (
            'expertise',
            'rank'
        )
        widgets = {
            'expertise': forms.HiddenInput(),
            'rank': forms.RadioSelect(
                choices=arbi_constants.EXPERTISE_RANKING
            )
        }

class CandidateReferenceForm(forms.ModelForm):
    class Meta:
        model = CandidateReference
        fields = (
            'name',
            'phone_number',
            'position',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-block', 'required': 'true', 'maxlength': 255}),
            'position': forms.TextInput(attrs={'class': 'input-block', 'required': 'true', 'maxlength': 255}),
            'phone_number': forms.TextInput(attrs={'class': 'input-block', 'required': 'true', 'maxlength': 20}),
        }
