# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0011_auto_20170616_0112'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='send_to_registration_first',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be directed to the registration page immediately after authenticating with the third party instead of the login page.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='send_to_registration_first',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be directed to the registration page immediately after authenticating with the third party instead of the login page.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='send_to_registration_first',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be directed to the registration page immediately after authenticating with the third party instead of the login page.'),
        ),
    ]
