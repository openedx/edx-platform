# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0024_re_populate_organization_metric_prompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.SmallIntegerField(default=1)),
                ('user', models.OneToOneField(related_name='registration_type', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
