# Convert the student.models.AnonymousUserId.course_id field from CourseKey to
# the more generic LearningContextKey.
#
# This migration does not produce any changes at the database level.

import opaque_keys.edx.django.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0038_auto_20201021_1256'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Do not actually make any changes to the database; the fields are identical string fields with the same
            # database properties.
            database_operations=[],
            # But update the migrator's view of the field to reflect the new field type.
            state_operations=[
                migrations.AlterField(
                    model_name='anonymoususerid',
                    name='course_id',
                    field=opaque_keys.edx.django.models.LearningContextKeyField(blank=True, db_index=True, max_length=255),
                ),
            ],
        ),
    ]
