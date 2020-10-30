# -*- coding: utf-8 -*-


import json
from django.db import migrations, models


def add_hide_linked_accounts_tab_to_sass_vars(apps, schema_editor):
    #
    SiteConfiguration = apps.get_model('site_configuration', 'SiteConfiguration')
    sites = SiteConfiguration.objects.all()
    for site in sites:
        exists = False
        for key, val in site.sass_variables:
            if key == '$hide-linked-accounts-tab':
                exists = True
                break

        if not exists:
            site.sass_variables.append(["$hide-linked-accounts-tab", ["false", "false"]])

        site.save()

class Migration(migrations.Migration):

    dependencies = [
        ('appsembler_sites', '0001_initial'),
        ('site_configuration', '0004_auto_20161120_2325')
    ]

    operations = [
        migrations.RunPython(add_hide_linked_accounts_tab_to_sass_vars),
    ]
