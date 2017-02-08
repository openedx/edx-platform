"""
Initial migration
"""
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Initial migration for CCXCon model
    """
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CCXCon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True, db_index=True)),
                ('oauth_client_id', models.CharField(max_length=255)),
                ('oauth_client_secret', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
    ]
