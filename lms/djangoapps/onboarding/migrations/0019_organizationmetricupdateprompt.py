# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0018_auto_20181115_0523'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationMetricUpdatePrompt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('latest_metric_submission', models.DateTimeField()),
                ('year', models.BooleanField(default=False)),
                ('year_month', models.BooleanField(default=False)),
                ('year_three_month', models.BooleanField(default=False)),
                ('year_six_month', models.BooleanField(default=False)),
                ('org', models.ForeignKey(related_name='organization_metrics_update_prompts', to='onboarding.Organization')),
                ('responsible_user', models.ForeignKey(related_name='organization_metrics_update_prompts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
