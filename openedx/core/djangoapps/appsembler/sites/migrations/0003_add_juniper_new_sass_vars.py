# -*- coding: utf-8 -*-


import json
from collections import OrderedDict

from django.db import migrations, models


def add_juniper_new_sass_vars(apps, schema_editor):
    """
    This migration adds all the new SASS variabled added during the initial
    pass of the Tahoe Juniper release upgrade.
    """
    new_sass_var_keys = OrderedDict(
        [
            ("$base-container-width", "calcRem(1200)"),
            ("$base-learning-container-width", "calcRem(1000)"),
            ("$courseware-content-container-side-padding", "calcRem(100)"),
            ("$courseware-content-container-sidebar-width", "calcRem(240)"),
            ("$courseware-content-container-width", "$base-learning-container-width"),
            ("$site-nav-width", "$base-container-width"),
            ("$inline-link-color", "$brand-primary-color"),
            ("$light-border-color", "#dedede"),
            ("$font-size-base-courseware", "calcRem(18)"),
            ("$line-height-base-courseware", "200%"),
            ("$in-app-container-border-radius", "calcRem(15)"),
            ("$login-register-container-width", "calcRem(480)")
            
        ]
    )
    SiteConfiguration = apps.get_model('site_configuration', 'SiteConfiguration')
    sites = SiteConfiguration.objects.all()
    for site in sites:
        for sass_var, sass_value in new_sass_var_keys.items():
            exists = False
            for key, val in site.sass_variables:
                if key == sass_var:
                    exists = True
                    break

            if not exists:
                site.sass_variables.append([sass_var, [sass_value, sass_value]])

        site.save()

class Migration(migrations.Migration):

    dependencies = [
        ('appsembler_sites', '0001_initial'),
        ('appsembler_sites', '0002_add_hide_linked_accounts_sass_var'),
        ('site_configuration', '0004_auto_20161120_2325'),
    ]

    operations = [
        migrations.RunPython(add_juniper_new_sass_vars),
    ]
