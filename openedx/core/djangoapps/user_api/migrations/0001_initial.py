import django.core.validators
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCourseTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255, db_index=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='UserOrgTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('key', models.CharField(max_length=255, db_index=True)),
                ('org', models.CharField(max_length=255, db_index=True)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(db_index=True, max_length=255, validators=[django.core.validators.RegexValidator('[-_a-zA-Z0-9]+')])),
                ('value', models.TextField()),
                ('user', models.ForeignKey(related_name='preferences', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userpreference',
            unique_together={('user', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='userorgtag',
            unique_together={('user', 'org', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='usercoursetag',
            unique_together={('user', 'course_id', 'key')},
        ),
    ]
