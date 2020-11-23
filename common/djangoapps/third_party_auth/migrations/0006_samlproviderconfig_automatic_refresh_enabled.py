# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0005_add_site_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderconfig',
            name='automatic_refresh_enabled',
            field=models.BooleanField(default=True, help_text=u"When checked, the SAML provider's metadata will be included in the automatic refresh job, if configured.", verbose_name=u'Enable automatic metadata refresh'),
        ),
    ]
