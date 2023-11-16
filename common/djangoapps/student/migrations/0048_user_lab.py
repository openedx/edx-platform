from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0047_user_field_student_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentLab',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('course_id', models.CharField(max_length=255)),
                ('block_id' , models.CharField(max_length=255)),
                ('result_student' , models.TextField(default=''))
            ],
            
        ),
    ]