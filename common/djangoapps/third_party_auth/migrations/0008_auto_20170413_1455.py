# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0007_auto_20170406_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='drop_existing_session',
            field=models.BooleanField(default=False, help_text='Whether to drop an existing session when accessing a view decorated with third_party_auth.decorators.tpa_hint_ends_existing_session when a tpa_hint URL query parameter mapping to this provider is included in the request.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='drop_existing_session',
            field=models.BooleanField(default=False, help_text='Whether to drop an existing session when accessing a view decorated with third_party_auth.decorators.tpa_hint_ends_existing_session when a tpa_hint URL query parameter mapping to this provider is included in the request.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='drop_existing_session',
            field=models.BooleanField(default=False, help_text='Whether to drop an existing session when accessing a view decorated with third_party_auth.decorators.tpa_hint_ends_existing_session when a tpa_hint URL query parameter mapping to this provider is included in the request.'),
        ),
    ]
