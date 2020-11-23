# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0017_remove_icon_class_image_secondary_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='send_welcome_email',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be sent a welcome email upon registration.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='send_welcome_email',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be sent a welcome email upon registration.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='send_welcome_email',
            field=models.BooleanField(default=False, help_text='If this option is selected, users will be sent a welcome email upon registration.'),
        ),
    ]
