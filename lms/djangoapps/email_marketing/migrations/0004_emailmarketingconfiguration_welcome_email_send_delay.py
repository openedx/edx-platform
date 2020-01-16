# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0003_auto_20160715_1145'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='welcome_email_send_delay',
            field=models.IntegerField(default=600, help_text='Number of seconds to delay the sending of User Welcome email after user has been activated'),
        ),
    ]
