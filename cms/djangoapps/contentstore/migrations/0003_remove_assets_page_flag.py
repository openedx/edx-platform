# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0002_add_assets_page_flag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coursenewassetspageflag',
            name='changed_by',
        ),
        migrations.RemoveField(
            model_name='newassetspageflag',
            name='changed_by',
        ),
        migrations.DeleteModel(
            name='CourseNewAssetsPageFlag',
        ),
        migrations.DeleteModel(
            name='NewAssetsPageFlag',
        ),
    ]
