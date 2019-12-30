# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0005_emailmarketingconfiguration_user_registration_cookie_timeout_delay'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='user_registration_cookie_timeout_delay',
            field=models.FloatField(default=3.0, help_text='The number of seconds to delay/timeout wait to get cookie values from sailthru.'),
        ),
    ]
