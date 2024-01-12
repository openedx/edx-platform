

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussions', '0017_discussionAction'),
    ]

    operations = [
        migrations.CreateModel(
            name='discussionTagThread',
           fields=[
            ('thread_id' , models.CharField(max_length=255)),
            ("user_id", models.IntegerField()),
            ('name_tag' , models.CharField(max_length=50))
            
        ],
 
        ),
    ]
