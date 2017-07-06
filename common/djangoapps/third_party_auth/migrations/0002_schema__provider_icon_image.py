# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='ltiproviderconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='oauth2providerconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
    ]
