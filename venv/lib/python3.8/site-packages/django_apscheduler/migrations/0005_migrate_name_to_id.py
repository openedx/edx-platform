from django.db import migrations


def migrate_name_to_id(apps, schema_editor):
    """
    Use DjangoJob.name as the database ID and primary key.
    """
    JobModel = apps.get_model("django_apscheduler", "DjangoJob")
    JobExecutionModel = apps.get_model("django_apscheduler", "DjangoJobExecution")
    migrated_id_mappings = {}
    migrated_job_executions = []

    # Copy 'name' to 'id'.
    for job in JobModel.objects.all():
        migrated_id_mappings[job.id] = job.name
        job.id = job.name
        job.name = f"{job.name}_tmp"
        job.save()

    # Update all job execution references
    for job_execution in JobExecutionModel.objects.filter(
        job_id__in=migrated_id_mappings
    ):
        job_execution.job_id = migrated_id_mappings[job_execution.job_id]
        migrated_job_executions.append(job_execution)

    JobExecutionModel.objects.bulk_update(migrated_job_executions, ["job_id"])

    # Remove old jobs
    JobModel.objects.filter(id__in=migrated_id_mappings).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("django_apscheduler", "0004_auto_20200717_1043"),
    ]

    operations = [migrations.RunPython(migrate_name_to_id)]
