from django.conf import settings
from django.db import models

# Backwards compatible settings.AUTH_USER_MODEL
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class UCSDCustomRegistration(models.Model):
    """
    This model contains two extra fields that will be saved when a user registers.
    The form that wraps this model is in the forms.py file.
    """
    user = models.OneToOneField(USER_MODEL, null=True)

    gender_nb = models.CharField(blank=False, max_length=16, verbose_name=b'Gender', choices=[
        (b'female', b'Female'), 
        (b'male', b'Male'), 
        (b'nonbinary', b'Non-Binary'),

        (b'decline', b'Decline to state'), 
        ])

    ethnicity = models.CharField(blank=False, max_length=16, verbose_name=b'Ethnicity', choices=[
        (b'aab', b'African American and black'), 
        (b'aian', b'American Indian / Alaska Native'), 
        (b'a', b'Asian'),
        (b'hl', b'Hispanic / Latinx'),
        (b'sana', b'Southwest Asia / North African'),
        (b'w', b'White'),

        (b'decline', b'Decline to state'), 
        ])

    age = models.CharField(blank=False, max_length=16, verbose_name=b'Age', choices=[
        (b'1317', b'13 - 17 years old'), 
        (b'1822', b'18 - 22 years old'), 
        (b'2329', b'23 - 29 years old'),
        (b'3049', b'30 - 49 years old'),
        (b'50plus', b'50+ years old'),

        (b'decline', b'Decline to state'), 
        ])

    education = models.CharField(blank=False, max_length=16, verbose_name=b'Highest level of education completed', choices=[
        (b'grad', b'Graduate'), 
        (b'undergrad', b'Undergrad'), 
        (b'highschool', b'Up to high school'),

        (b'decline', b'Decline to state'), 
        ])

    howheard = models.CharField(blank=False, max_length=16, verbose_name=b'How did you hear about UC San Diego Online', choices=[
        (b'socialmedia', b'Social media'), 
        (b'email', b'Email'), 
        (b'wom', b'Word-of-mouth'),
        (b'print', b'Print advertisement'),
        (b'other', b'Other'), 
        ])

    class Meta:
        verbose_name = "Demographic Information"
        verbose_name_plural = "Demographic Information"
