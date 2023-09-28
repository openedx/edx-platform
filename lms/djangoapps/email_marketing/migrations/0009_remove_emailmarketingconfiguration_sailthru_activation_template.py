from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0008_auto_20170809_0539'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailmarketingconfiguration',
            name='sailthru_activation_template',
        ),
    ]
