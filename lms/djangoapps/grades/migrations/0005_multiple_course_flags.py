# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0004_visibleblocks_course_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursepersistentgradesflag',
            name='course_id',
            field=CourseKeyField(max_length=255, db_index=True),
        ),
    ]

    def unapply(self, project_state, schema_editor, collect_sql=False):
        """
        This is a bit of a hack. This migration is removing a unique index that was erroneously included in the initial
        migrations for this app, so it's very likely that IntegrityErrors would result if we did roll this particular
        migration back. To avoid this, we override the default unapply method and skip the addition of a unique index
        that was never intended to exist.

        The assumption here is that you are never going to be specifically targeting a migration < 0005 for grades,
        and will only ever be migrating backwards if you intend to go all the way back to zero and drop the tables.

        If this is not the case and you are reading this comment, please file a PR to help us with your intended usage.
        """
        pass
