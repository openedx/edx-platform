# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('student', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=255, db_index=True)),
                ('active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Link Course',
                'verbose_name_plural': 'Link Courses',
            },
        ),
        migrations.AlterUniqueTogether(
            name='organizationuser',
            unique_together=set([('user_id', 'organization')]),
        ),
    ]
