from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0008_programsapiconfig_program_details_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='marketing_path',
            field=models.CharField(help_text='Path used to construct URLs to programs marketing pages (e.g., "/foo").', max_length=255, blank=True),
        ),
    ]
