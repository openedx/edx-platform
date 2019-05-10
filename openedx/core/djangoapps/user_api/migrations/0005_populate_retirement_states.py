# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from openedx.core.djangoapps.user_api.management.commands.populate_retirement_states import Command


def populate_retirement_state_handler():
    command = Command()
    command.handle()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user_api', '0004_userretirementpartnerreportingstatus'),
    ]

    operations = [
        migrations.RunPython(Command().handle)
    ]
