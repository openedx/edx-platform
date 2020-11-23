# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20170111_0422'),
    ]

    # This migration was to add a constraint that we lost in the Django
    # 1.4->1.8 upgrade. But since the constraint used to be created, production
    # would already have the constraint even before running the migration, and
    # running the migration would fail. We needed to make the migration
    # idempotent.  Instead of reverting this migration while we did that, we
    # edited it to be a SQL no-op, so that people who had already applied it
    # wouldn't end up with a ghost migration.

    # It had been:
    #
    # migrations.RunSQL(
    #   "create unique index email on auth_user (email);",
    #   "drop index email on auth_user;"
    # )

    operations = [
        # Nothing to do.
    ]
