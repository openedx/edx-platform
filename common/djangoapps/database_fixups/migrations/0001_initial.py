from django.db import migrations, models

# We used to have a uniqueness constraint on auth_user.email:
# https://github.com/openedx/edx-platform/commit/c52727b0e0fb241d8211900975d3b69fe5a1bd57
#
# That constraint was lost in the upgrade from Django 1.4->1.8.  This migration
# adds it back.  But because it might already exist in databases created
# long-enough ago, we have to do it idempotently.  So we check for the
# existence of the constraint before creating it.

def add_email_uniqueness_constraint(apps, schema_editor):
    # Do we already have an email uniqueness constraint?
    cursor = schema_editor.connection.cursor()
    constraints = schema_editor.connection.introspection.get_constraints(cursor, "auth_user")
    email_constraint = constraints.get("email", {})
    if email_constraint.get("columns") == ["email"] and email_constraint.get("unique") == True:
        # We already have the constraint, we're done.
        return

    # We don't have the constraint, make it.
    schema_editor.execute("create unique index email on auth_user (email)")


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(add_email_uniqueness_constraint, atomic=False)
    ]
