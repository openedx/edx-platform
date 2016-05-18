# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160518_0914'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organizationuser',
            options={'verbose_name': 'Link Organization', 'verbose_name_plural': 'Link Organizations'},
        ),
        migrations.AlterField(
            model_name='organizationuser',
            name='user_id',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
