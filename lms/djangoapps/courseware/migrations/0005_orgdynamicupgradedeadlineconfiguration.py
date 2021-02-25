import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import lms.djangoapps.courseware.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courseware', '0004_auto_20171010_1639'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrgDynamicUpgradeDeadlineConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('org_id', models.CharField(max_length=255, db_index=True)),
                ('deadline_days', models.PositiveSmallIntegerField(default=21, help_text='Number of days a learner has to upgrade after content is made available')),
                ('opt_out', models.BooleanField(default=False, help_text='Disable the dynamic upgrade deadline for this organization.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
            bases=(lms.djangoapps.courseware.models.OptOutDynamicUpgradeDeadlineMixin, models.Model),
        ),
        migrations.AlterModelOptions(
            name='coursedynamicupgradedeadlineconfiguration',
            options={'ordering': ('-change_date',)},
        ),
    ]
