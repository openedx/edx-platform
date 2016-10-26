# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0006_data_sharing_consent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ltiproviderconfig',
            name='data_sharing_consent',
        ),
        migrations.RemoveField(
            model_name='oauth2providerconfig',
            name='data_sharing_consent',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='data_sharing_consent',
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='enable_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='This field is used to determine whether data sharing consent is enabled or disabled of users signing in using this SSO provider. If disabled, consent will not be requested, and course data will not be shared.'),
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text='This field is used to determine the place from where user must consent to data sharing in order to proceed.', max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='enable_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='This field is used to determine whether data sharing consent is enabled or disabled of users signing in using this SSO provider. If disabled, consent will not be requested, and course data will not be shared.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text='This field is used to determine the place from where user must consent to data sharing in order to proceed.', max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='enable_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='This field is used to determine whether data sharing consent is enabled or disabled of users signing in using this SSO provider. If disabled, consent will not be requested, and course data will not be shared.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='enforce_data_sharing_consent',
            field=models.CharField(default=b'optional', help_text='This field is used to determine the place from where user must consent to data sharing in order to proceed.', max_length=25, choices=[(b'optional', b'Optional'), (b'at_login', b'At Login'), (b'at_enrollment', b'At Enrollment')]),
        ),
    ]
