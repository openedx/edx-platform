from django.db import migrations, models


def migrate_data_forwards(apps, schema_editor):
    EmailMarketingConfiguration = apps.get_model('email_marketing', 'EmailMarketingConfiguration')
    EmailMarketingConfiguration.objects.all().update(
        sailthru_welcome_template=models.F('sailthru_activation_template')
    )


def migrate_data_backwards(apps, schema_editor):
    # Just copying old field's value to new one in forward migration, so nothing needed here.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0007_auto_20170809_0653'),
    ]

    operations = [
        migrations.RunPython(migrate_data_forwards, migrate_data_backwards)
    ]
