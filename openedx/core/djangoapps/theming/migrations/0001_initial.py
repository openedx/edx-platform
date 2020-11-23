# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteTheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('theme_dir_name', models.CharField(max_length=255)),
                ('site', models.ForeignKey(related_name='themes', to='sites.Site', on_delete=models.CASCADE)),
            ],
        ),
    ]
