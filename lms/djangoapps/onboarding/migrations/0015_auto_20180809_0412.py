# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


class Migration(migrations.Migration):

    def add_missing_email_preferences(apps, schema_editor):
        """
        Add missing email preferences for users
        :param schema_editor:
        :return:
        """
        User = apps.get_model('auth', 'User')
        EmailPreference = apps.get_model('onboarding', 'EmailPreference')

        users = User.objects.all()
        for user in users:
            ep, is_created = EmailPreference.objects.get_or_create(user=user)
            print(", ".join([user.email, str(is_created)]))

    dependencies = [
        ('onboarding', '0014_emailpreference'),
    ]

    operations = [
        migrations.RunPython(add_missing_email_preferences),
    ]
