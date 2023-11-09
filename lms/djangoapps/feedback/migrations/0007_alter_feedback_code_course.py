

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_alter_feedback_course_id'),
    ]

    operations = [
         
        migrations.RenameField(
            model_name='feedback',
            old_name = 'course_id' ,
            new_name = 'course_code',

        )
        
    ]