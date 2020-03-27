from django.conf import settings
from django.db import models


# Backwards compatible settings.AUTH_USER_MODEL
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class AdditionalRegistrationFields(models.Model):
    """
    This model contains two extra fields that will be saved when a user registers.
    The form that wraps this model is in the forms.py file.
    """
    user = models.OneToOneField(USER_MODEL, null=True, on_delete=models.SET_NULL)

    gender_nb = models.CharField(blank=False, max_length=32, verbose_name=b'Gender', choices=[
        (b'male', b'Male'),
        (b'female', b'Female'),
        (b'nonbinary', b'Non-Binary'),

        (b'decline', b'Decline to State'),
    ])

    ethnicity = models.CharField(blank=False, max_length=128, verbose_name=b'Ethnicity', choices=[
        (b'african-american-and-black', b'African American and Black'),
        (b'american-indian-alaska-native', b'American Indian / Alaska Native'),
        (b'asian', b'Asian'),
        (b'hispanic-latinx', b'Hispanic / Latinx'),
        (b'native-hawaiian-and-pacific-islander', b'Native Hawaiian and Pacific Islander'),
        (b'southwest-asia-north-african', b'Southwest Asia / North African'),
        (b'white', b'White'),

        (b'decline', b'Decline to State'),
    ])

    age = models.CharField(blank=False, max_length=32, verbose_name=b'Age', choices=[
        (b'13-17', b'13 - 17 years old'),
        (b'18-22', b'18 - 22 years old'),
        (b'23-29', b'23 - 29 years old'),
        (b'30-49', b'30 - 49 years old'),
        (b'50-plus', b'50+ years old'),

        (b'decline', b'Decline to State'),
    ])

    education = models.CharField(blank=False, max_length=64, verbose_name=b'Highest level of education completed', choices=[
        (b'graduate', b'Graduate'),
        (b'undergraduate', b'Undergraduate'),
        (b'up-to-high-school', b'Up to High School'),

        (b'decline', b'Decline to State'),
    ])

    howheard = models.CharField(blank=False, max_length=64, verbose_name=b'How did you hear about UC San Diego Online', choices=[
        (b'social-media', b'Social Media'),
        (b'email', b'Email'),
        (b'word-of-mouth', b'Word-of-Mouth'),
        (b'print-advertisement', b'Print Advertisement'),
        (b'other', b'Other'),
    ])

    class Meta:
        verbose_name = "Additional Registration Information"
        verbose_name_plural = "Additional Registration Information"
