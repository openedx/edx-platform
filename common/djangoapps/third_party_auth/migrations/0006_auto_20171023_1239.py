# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('third_party_auth', '0005_add_site_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSocialAuthMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uid', models.CharField(max_length=255)),
                ('puid', models.CharField(max_length=200)),
                ('user', models.ForeignKey(related_name='third_party_auth', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'third_party_auth_social_auth_mapping',
            },
        ),
        migrations.AlterUniqueTogether(
            name='usersocialauthmapping',
            unique_together=set([('uid', 'puid')]),
        ),
    ]
