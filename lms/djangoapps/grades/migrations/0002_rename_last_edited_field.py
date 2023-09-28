from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='persistentsubsectiongrade',
            old_name='subtree_edited_date',
            new_name='subtree_edited_timestamp',
        ),
    ]
