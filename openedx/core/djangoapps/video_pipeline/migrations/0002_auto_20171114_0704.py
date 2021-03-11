from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_pipeline', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='videopipelineintegration',
            name='client_name',
            field=models.CharField(default='VEDA-Prod', help_text='Oauth client name of video pipeline service.', max_length=100),
        ),
        migrations.AlterField(
            model_name='videopipelineintegration',
            name='service_username',
            field=models.CharField(default='veda_service_user', help_text='Username created for Video Pipeline Integration, e.g. veda_service_user.', max_length=100),
        ),
    ]
