from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_goals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursegoal',
            name='goal_key',
            field=models.CharField(default='unsure', max_length=100, choices=[('certify', 'Earn a certificate'), ('complete', 'Complete the course'), ('explore', 'Explore the course'), ('unsure', 'Not sure yet')]),
        ),
    ]
