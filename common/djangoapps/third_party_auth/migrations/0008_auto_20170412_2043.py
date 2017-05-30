# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0007_auto_20170406_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderdata',
            name='slo_binding',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'SLO binding type', choices=[('', '---------'), (b'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect', b'HTTP-Redirect'), (b'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST', b'HTTP-POST')]),
        ),
        migrations.AddField(
            model_name='samlproviderdata',
            name='slo_url',
            field=models.URLField(null=True, verbose_name=b'Single Log-Out URL', blank=True),
        ),
    ]
