# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0022_auto_20190211_0950'),
        ('oef', '0011_auto_20180312_1021'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationOefUpdatePrompt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('latest_finish_date', models.DateTimeField()),
                ('year', models.BooleanField(default=False)),
                ('org', models.ForeignKey(related_name='organization_oef_update_prompts', to='onboarding.Organization')),
                ('responsible_user', models.ForeignKey(related_name='organization_oef_update_prompts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
