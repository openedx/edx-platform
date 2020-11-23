# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0011_certificatetemplate_alter_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificategenerationcoursesetting',
            name='include_hours_of_effort',
            field=models.NullBooleanField(default=None, help_text="Display estimated time to complete the course, which is equal to the maximum hours of effort per week times the length of the course in weeks. This attribute will only be displayed in a certificate when the attributes 'Weeks to complete' and 'Max effort' have been provided for the course run and its certificate template includes Hours of Effort."),
        ),
    ]
