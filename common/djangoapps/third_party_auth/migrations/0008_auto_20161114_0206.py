# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0007_auto_20161107_0541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ltiproviderconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text="This field determines if data sharing consent is optional, if it's required at login, or if it's required when registering for courses.", max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
        migrations.AlterField(
            model_name='oauth2providerconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text="This field determines if data sharing consent is optional, if it's required at login, or if it's required when registering for courses.", max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text="This field determines if data sharing consent is optional, if it's required at login, or if it's required when registering for courses.", max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
    ]
