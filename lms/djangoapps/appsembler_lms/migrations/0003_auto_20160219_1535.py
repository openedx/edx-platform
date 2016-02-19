# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('appsembler_lms', '0002_organization_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='display_name',
            field=models.CharField(help_text='The display name of this organization.', max_length=128),
        ),
        migrations.AlterField(
            model_name='organization',
            name='users',
            field=models.ManyToManyField(help_text='List of users in an organization', related_name='organizations', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
