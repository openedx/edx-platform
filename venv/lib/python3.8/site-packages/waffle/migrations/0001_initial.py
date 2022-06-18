# -*- coding: utf-8 -*-
from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The human/computer readable name.', unique=True, max_length=100)),
                ('everyone', models.NullBooleanField(help_text='Flip this flag on (Yes) or off (No) for everyone, overriding all other settings. Leave as Unknown to use normally.')),
                ('percent', models.DecimalField(help_text='A number between 0.0 and 99.9 to indicate a percentage of users for whom this flag will be active.', null=True, max_digits=3, decimal_places=1, blank=True)),
                ('testing', models.BooleanField(default=False, help_text='Allow this flag to be set for a session for user testing.')),
                ('superusers', models.BooleanField(default=True, help_text='Flag always active for superusers?')),
                ('staff', models.BooleanField(default=False, help_text='Flag always active for staff?')),
                ('authenticated', models.BooleanField(default=False, help_text='Flag always active for authenticate users?')),
                ('languages', models.TextField(default='', help_text='Activate this flag for users with one of these languages (comma separated list)', blank=True)),
                ('rollout', models.BooleanField(default=False, help_text='Activate roll-out mode?')),
                ('note', models.TextField(help_text='Note where this Flag is used.', blank=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Flag was created.', db_index=True)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Flag was last modified.')),
                ('groups', models.ManyToManyField(help_text='Activate this flag for these user groups.', to='auth.Group', blank=True)),
                ('users', models.ManyToManyField(help_text='Activate this flag for these users.', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The human/computer readable name.', unique=True, max_length=100)),
                ('percent', models.DecimalField(help_text='A number between 0.0 and 100.0 to indicate a percentage of the time this sample will be active.', max_digits=4, decimal_places=1)),
                ('note', models.TextField(help_text='Note where this Sample is used.', blank=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Sample was created.', db_index=True)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Sample was last modified.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The human/computer readable name.', unique=True, max_length=100)),
                ('active', models.BooleanField(default=False, help_text='Is this flag active?')),
                ('note', models.TextField(help_text='Note where this Switch is used.', blank=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Switch was created.', db_index=True)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Switch was last modified.')),
            ],
            options={
                'verbose_name_plural': 'Switches',
            },
            bases=(models.Model,),
        ),
    ]
