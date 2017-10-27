# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding_survey', '0013_auto_20170912_0344'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtendedProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=256)),
                ('last_name', models.CharField(max_length=256)),
                ('is_poc', models.BooleanField(default=0)),
                ('is_currently_employed', models.BooleanField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('point_of_contact_exist', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='extendedprofile',
            name='organization',
            field=models.ForeignKey(related_name='extended_profile', blank=True, to='onboarding_survey.Organization', null=True),
        ),
        migrations.AddField(
            model_name='extendedprofile',
            name='user',
            field=models.OneToOneField(related_name='extended_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
