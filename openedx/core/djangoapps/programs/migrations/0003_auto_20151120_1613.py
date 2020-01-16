# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0002_programsapiconfig_cache_ttl'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='authoring_app_css_path',
            field=models.CharField(
                max_length=255,
                help_text='This value is required in order to enable the Studio authoring interface.',
                verbose_name="Path to authoring app's CSS",
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='programsapiconfig',
            name='authoring_app_js_path',
            field=models.CharField(
                max_length=255,
                help_text='This value is required in order to enable the Studio authoring interface.',
                verbose_name="Path to authoring app's JS",
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='programsapiconfig',
            name='enable_studio_tab',
            field=models.BooleanField(default=False, verbose_name='Enable Studio Authoring Interface'),
        ),
        migrations.AlterField(
            model_name='programsapiconfig',
            name='enable_student_dashboard',
            field=models.BooleanField(default=False, verbose_name='Enable Student Dashboard Displays'),
        ),
    ]
