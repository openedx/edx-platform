from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0006_programsapiconfig_xseries_ad_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='program_listing_enabled',
            field=models.BooleanField(default=False, verbose_name='Do we want to show program listing page'),
        ),
    ]
