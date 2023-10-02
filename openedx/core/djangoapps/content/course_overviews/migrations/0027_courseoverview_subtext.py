
from django.db import migrations, models

from opaque_keys.edx.django.models import  UsageKeyField
class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0026_courseoverview_entrance_exam'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOverviewSubText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_overview', models.ForeignKey(related_name='tabs', to='course_overviews.CourseOverview', on_delete=models.CASCADE)),
                ('usage_key', UsageKeyField(max_length=255)),
                ('title' ,  models.CharField(max_length=1000)),
                ('sub_text' , models.TextField())
            ],
        ),
    ]
