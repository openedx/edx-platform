# -*- coding: utf-8 -*-


from openedx.core.lib.hash_utils import short_token
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lti_provider', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_secret',
            field=models.CharField(default=short_token, unique=True, max_length=32),
        ),
    ]
