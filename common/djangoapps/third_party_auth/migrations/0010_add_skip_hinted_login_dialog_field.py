# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0009_auto_20170415_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='skip_hinted_login_dialog',
            field=models.BooleanField(default=False, help_text='If this option is enabled, users that visit a "TPA hinted" URL for this provider (e.g. a URL ending with `?tpa_hint=[provider_name]`) will be forwarded directly to the login URL of the provider instead of being first prompted with a login dialog.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='skip_hinted_login_dialog',
            field=models.BooleanField(default=False, help_text='If this option is enabled, users that visit a "TPA hinted" URL for this provider (e.g. a URL ending with `?tpa_hint=[provider_name]`) will be forwarded directly to the login URL of the provider instead of being first prompted with a login dialog.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='skip_hinted_login_dialog',
            field=models.BooleanField(default=False, help_text='If this option is enabled, users that visit a "TPA hinted" URL for this provider (e.g. a URL ending with `?tpa_hint=[provider_name]`) will be forwarded directly to the login URL of the provider instead of being first prompted with a login dialog.'),
        ),
    ]
