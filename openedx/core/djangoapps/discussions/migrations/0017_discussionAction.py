

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussions', '0016_discussionReport'),
    ]

    operations = [
        migrations.CreateModel(
            name='discussionActions',
           fields=[
            ("user_id", models.IntegerField()),
            ('thread_id' , models.CharField(max_length=255)),
            ('is_best_thread' , models.BooleanField(default=False)),
            
        ],
 
        ),
    ]
