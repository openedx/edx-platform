from django.db import migrations, connection
 
def rename_index_if_postgres(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        # Skip for MySQL
        return
 
    # For PostgreSQL: run raw SQL to rename the index
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            ALTER INDEX coursewarehistoryextended_studentmodulehistoryextended_student_module_id_abc123
            RENAME TO student_module_idx;
        """)
 
class Migration(migrations.Migration):
 
    dependencies = [
        ('coursewarehistoryextended', '0002_force_studentmodule_index'),
    ]
 
    operations = [
        migrations.RunPython(rename_index_if_postgres, reverse_code=migrations.RunPython.noop),
    ]