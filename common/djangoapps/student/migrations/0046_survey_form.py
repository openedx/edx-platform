from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0045_last_history_activte_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='survey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_survey', models.CharField(max_length=225)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],   
        ),
        migrations.CreateModel(
            name='surveyQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.survey')),
                ('question',models.CharField(max_length=225, null=True)),
                ('type', models.CharField(max_length=32)),
                ('config' , models.JSONField(null=True))
            ]
        ),
        migrations.CreateModel(
            name='surveyCourse', 
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(db_constraint=False, null=True, blank=True ,on_delete=django.db.models.deletion.CASCADE, to='course_overviews.CourseOverview')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.survey')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
            ]
        ),
        migrations.CreateModel(
            name='surveyUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question' , models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.surveyQuestion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('answer_text', models.CharField( max_length=255, null=True)),
            ]
        )
    ]