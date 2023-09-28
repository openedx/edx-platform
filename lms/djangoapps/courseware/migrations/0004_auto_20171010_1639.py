from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0003_auto_20170825_0935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursedynamicupgradedeadlineconfiguration',
            name='opt_out',
            field=models.BooleanField(default=False, help_text='Disable the dynamic upgrade deadline for this course run.'),
        ),
    ]
