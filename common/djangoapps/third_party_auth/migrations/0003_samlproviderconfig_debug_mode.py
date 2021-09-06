# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0002_schema__provider_icon_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderconfig',
            name='debug_mode',
            field=models.BooleanField(default=False, help_text=u'In debug mode, all SAML XML requests and responses will be logged. This is helpful for testing/setup but should always be disabled before users start using this provider.', verbose_name=u'Debug Mode'),
        ),
    ]
