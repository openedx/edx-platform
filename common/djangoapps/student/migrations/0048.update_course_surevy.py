

from django.db import migrations, models

import django.db.models.deletion



class Migration(migrations.Migration):

    dependencies = [
        ('student', '0047_form_survey'),
    ]

    operations = [
        migrations.AddField(
            model_name='listSurveyQuestion',
            name='course',
            field=models.ForeignKey(db_constraint=False,null=True,blank=True ,on_delete=django.db.models.deletion.CASCADE, to='course_overviews.CourseOverview')
        ),
        migrations.AddField(
            model_name='listSurveyQuestion',
            name='isActive' ,
            field=models.BooleanField(default=False)
        )
        ,
        migrations.AddField(
            model_name='surveyForm',
            name='course',
            field=models.ForeignKey(db_constraint=False,null=True,blank=True ,on_delete=django.db.models.deletion.CASCADE, to='course_overviews.CourseOverview')
        )
    ]
