# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from oauth2_provider.settings import oauth2_settings


def migrate_restricted_flag(apps, schema_editor):
    RestrictedApplication = apps.get_model('oauth_dispatch', 'RestrictedApplication')

    for restricted_application in RestrictedApplication.objects.all():
        application = restricted_application.application
        application.restricted = True
        application.save()


class Migration(migrations.Migration):
    dependencies = [
        ('oauth_dispatch', '0002_application'),
        migrations.swappable_dependency(oauth2_settings.APPLICATION_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='restricted',
            field=models.BooleanField(default=False,
                                      help_text='Restricted clients receive expired access tokens. They are intended to provide identity information to third-parties.'),
        ),
        migrations.RunPython(migrate_restricted_flag, migrations.RunPython.noop)
    ]
