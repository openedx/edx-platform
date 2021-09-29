from django.db import migrations, models
from django.db.utils import IntegrityError


from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from ..models import SplitModulestoreCourseIndex as SplitModulestoreCourseIndex_Real


def forwards_func(apps, schema_editor):
    """
    Copy all course index data from MongoDB to MySQL.
    """
    db_alias = schema_editor.connection.alias
    SplitModulestoreCourseIndex = apps.get_model("split_modulestore_django", "SplitModulestoreCourseIndex")
    split_modulestore = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)

    for course_index in split_modulestore.db_connection.find_matching_course_indexes(force_mongo=True):
        data = SplitModulestoreCourseIndex_Real.fields_from_v1_schema(course_index)

        SplitModulestoreCourseIndex(**data).save(using=db_alias)

def reverse_func(apps, schema_editor):
    """
    Reverse the data migration, deleting all entries in this table.
    """
    db_alias = schema_editor.connection.alias
    SplitModulestoreCourseIndex = apps.get_model("split_modulestore_django", "SplitModulestoreCourseIndex")
    SplitModulestoreCourseIndex.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('split_modulestore_django', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
