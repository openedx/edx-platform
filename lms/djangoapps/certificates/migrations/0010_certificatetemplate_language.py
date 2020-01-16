# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0009_certificategenerationcoursesetting_language_self_generation'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificatetemplate',
            name='language',
            field=models.CharField(help_text='Only certificates for courses in the selected language will be rendered using this template. Course language is determined by the first two letters of the language code.', max_length=2, null=True, blank=True),
        ),
    ]
