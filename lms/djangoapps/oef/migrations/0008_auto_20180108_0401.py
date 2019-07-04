# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0007_auto_20180107_1531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useranswers',
            name='question',
        ),
        migrations.RemoveField(
            model_name='useranswers',
            name='selected_option',
        ),
        migrations.RemoveField(
            model_name='useranswers',
            name='user_survey',
        ),
        migrations.RemoveField(
            model_name='useroefsurvey',
            name='survey',
        ),
        migrations.RemoveField(
            model_name='useroefsurvey',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserAnswers',
        ),
        migrations.DeleteModel(
            name='UserOefSurvey',
        ),
    ]
