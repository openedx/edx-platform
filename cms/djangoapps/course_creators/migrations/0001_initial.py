# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCreator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state_changed', models.DateTimeField(help_text='The date when state was last updated', verbose_name=b'state last updated', auto_now_add=True)),
                ('state', models.CharField(default=b'unrequested', help_text='Current course creator state', max_length=24, choices=[(b'unrequested', 'unrequested'), (b'pending', 'pending'), (b'granted', 'granted'), (b'denied', 'denied')])),
                ('note', models.CharField(help_text='Optional notes about this user (for example, why course creation access was denied)', max_length=512, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, help_text='Studio user')),
            ],
        ),
    ]
