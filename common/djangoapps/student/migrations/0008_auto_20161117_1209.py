from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_registrationcookieconfiguration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='level_of_education',
            field=models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[('p', 'Doctorate'), ('m', "Master's or professional degree"), ('b', "Bachelor's degree"), ('a', 'Associate degree'), ('hs', 'Secondary/high school'), ('jhs', 'Junior secondary/junior high/middle school'), ('el', 'Elementary/primary school'), ('none', 'No formal education'), ('other', 'Other education')]),
        ),
    ]
