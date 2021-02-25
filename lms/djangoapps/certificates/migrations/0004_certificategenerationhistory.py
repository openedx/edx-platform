import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('instructor_task', '0001_initial'),
        ('certificates', '0003_data__default_modes'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateGenerationHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_id', CourseKeyField(max_length=255)),
                ('is_regeneration', models.BooleanField(default=False)),
                ('generated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('instructor_task', models.ForeignKey(to='instructor_task.InstructorTask', on_delete=models.CASCADE)),
            ],
        ),
    ]
