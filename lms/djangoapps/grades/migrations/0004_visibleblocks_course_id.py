from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0003_coursepersistentgradesflag_persistentgradesenabledflag'),
    ]

    operations = [
        migrations.AddField(
            model_name='visibleblocks',
            name='course_id',
            field=CourseKeyField(default=CourseKey.from_string('edX/BerylMonkeys/TNL-5458'), max_length=255, db_index=True),
            preserve_default=False,
        ),
    ]
