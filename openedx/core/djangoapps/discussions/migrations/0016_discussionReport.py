

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussions', '0015_discussiontopiclink_context'),
    ]

    operations = [
        migrations.CreateModel(
            name='discussionreport',
           fields=[
            ("thread_id", models.CharField(max_length=255)),
            ("user_id", models.IntegerField()),
            ("report_type", models.CharField(max_length=255)),
            ("report_details", models.TextField()),  
        ],
 
        ),
    ]
