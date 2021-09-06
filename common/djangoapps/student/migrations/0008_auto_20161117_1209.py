# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_registrationcookieconfiguration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='level_of_education',
            field=models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(u'p', u'Doctorate'), (u'm', u"Master's or professional degree"), (u'b', u"Bachelor's degree"), (u'a', u'Associate degree'), (u'hs', u'Secondary/high school'), (u'jhs', u'Junior secondary/junior high/middle school'), (u'el', u'Elementary/primary school'), (u'none', u'No formal education'), (u'other', u'Other education')]),
        ),
    ]
