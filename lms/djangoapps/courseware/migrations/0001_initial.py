import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import BlockTypeKeyField, CourseKeyField, UsageKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfflineComputedGrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('gradeset', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='OfflineComputedGradeLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('seconds', models.IntegerField(default=0)),
                ('nstudents', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='StudentFieldOverride',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('location', UsageKeyField(max_length=255, db_index=True)),
                ('field', models.CharField(max_length=255)),
                ('value', models.TextField(default='null')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='StudentModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module_type', models.CharField(default='problem', max_length=32, db_index=True, choices=[('problem', 'problem'), ('video', 'video'), ('html', 'html'), ('course', 'course'), ('chapter', 'Section'), ('sequential', 'Subsection'), ('library_content', 'Library Content')])),
                ('module_state_key', UsageKeyField(max_length=255, db_column='module_id', db_index=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(db_index=True, null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('done', models.CharField(default='na', max_length=8, db_index=True, choices=[('na', 'NOT_APPLICABLE'), ('f', 'FINISHED'), ('i', 'INCOMPLETE')])),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='StudentModuleHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('student_module', models.ForeignKey(to='courseware.StudentModule', on_delete=models.CASCADE)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='XModuleStudentInfoField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default='null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='XModuleStudentPrefsField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default='null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('module_type', BlockTypeKeyField(max_length=64, db_index=True)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='XModuleUserStateSummaryField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64, db_index=True)),
                ('value', models.TextField(default='null')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('usage_id', UsageKeyField(max_length=255, db_index=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='xmoduleuserstatesummaryfield',
            unique_together={('usage_id', 'field_name')},
        ),
        migrations.AlterUniqueTogether(
            name='xmodulestudentprefsfield',
            unique_together={('student', 'module_type', 'field_name')},
        ),
        migrations.AlterUniqueTogether(
            name='xmodulestudentinfofield',
            unique_together={('student', 'field_name')},
        ),
        migrations.AlterUniqueTogether(
            name='studentmodule',
            unique_together={('student', 'module_state_key', 'course_id')},
        ),
        migrations.AlterUniqueTogether(
            name='studentfieldoverride',
            unique_together={('course_id', 'field', 'location', 'student')},
        ),
        migrations.AlterUniqueTogether(
            name='offlinecomputedgrade',
            unique_together={('user', 'course_id')},
        ),
    ]
