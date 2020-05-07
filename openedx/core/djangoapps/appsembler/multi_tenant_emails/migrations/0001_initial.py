# -*- coding: utf-8 -*-
from django.db import migrations, models


def remove_user_email_uniqueness_constraint(apps, schema_editor):
    """
    Enable multi-tenant emails.

    To revert this migration, run the following code (untested):
        SQL> alter table auth_user drop index email, add unique index `email` (`email`);
        $ ./manage.py lms migrate multi_tenant_emails zero --fake

    Then disable this application by removing it from INSTALLED_APPS (or ADDL_INSTALLED_APPS).
    """
    # Do we already have an email uniqueness constraint?
    cursor = schema_editor.connection.cursor()
    constraints = schema_editor.connection.introspection.get_constraints(cursor, "auth_user")
    email_constraint = constraints.get("email", {})
    if email_constraint.get("columns") == ["email"] and email_constraint.get("unique") == True:
        # There is a UNIQUE constraint, but we need multi-tenant emails instead.
        # Let's make it a regular index to retain the performance of it.
        schema_editor.execute("alter table auth_user drop index email, add index `email` (`email`)")


class Migration(migrations.Migration):

    dependencies = [
        ('database_fixups', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_user_email_uniqueness_constraint, atomic=False)
    ]
