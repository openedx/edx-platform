from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0005_programsapiconfig_max_retries'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='xseries_ad_enabled',
            field=models.BooleanField(default=False, verbose_name='Do we want to show xseries program advertising'),
        ),
    ]
