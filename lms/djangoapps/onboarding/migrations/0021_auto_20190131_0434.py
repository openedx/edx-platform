# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0020_populate_organization_metric_prompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetricUpdatePromptRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('click', models.CharField(db_index=True, max_length=3, null=True, choices=[(b'RML', b'Remind Me Later'), (b'TMT', b'Take Me There'), (b'NT', b"No Thanks, I'm not interested")])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='organizationmetricupdateprompt',
            name='remind_me_later',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='metricupdatepromptrecord',
            name='prompt',
            field=models.ForeignKey(related_name='metrics_update_prompt_records', to='onboarding.OrganizationMetricUpdatePrompt'),
        ),
    ]
