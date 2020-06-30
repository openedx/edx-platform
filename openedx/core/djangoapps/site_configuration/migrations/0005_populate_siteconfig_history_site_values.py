# -*- coding: utf-8 -*-


from django.db import migrations

forward_sql = """
UPDATE
    site_configuration_siteconfigurationhistory
SET
    site_values = '{}';
"""

reverse_sql = """
UPDATE
    site_configuration_siteconfigurationhistory
SET
    site_values = '';
"""


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0004_add_site_values_field'),
    ]

    operations = [
        migrations.RunSQL(forward_sql, reverse_sql=reverse_sql),
    ]
