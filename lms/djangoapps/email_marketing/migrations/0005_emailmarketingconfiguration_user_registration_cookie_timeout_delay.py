# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0004_emailmarketingconfiguration_welcome_email_send_delay'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='user_registration_cookie_timeout_delay',
            field=models.FloatField(default=1.5, help_text='The number of seconds to delay/timeout wait to get cookie values from sailthru.'),
        ),
    ]
