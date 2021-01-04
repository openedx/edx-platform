# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0010_auto_20170204_2332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='api_version_number',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='authoring_app_css_path',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='authoring_app_js_path',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='cache_ttl',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='enable_certification',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='enable_student_dashboard',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='enable_studio_tab',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='internal_service_url',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='max_retries',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='program_details_enabled',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='program_listing_enabled',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='public_service_url',
        ),
        migrations.RemoveField(
            model_name='programsapiconfig',
            name='xseries_ad_enabled',
        ),
    ]
