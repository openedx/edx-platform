"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from projects.models import Project, WorkgroupReview, WorkgroupPeerReview, WorkgroupSubmissionReview

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):

        log.warning('Migrating Projects...')
        projects = Project.objects.all()
        for project in projects:
            current_course_id = project.course_id
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = current_course_id.replace("+", "/")
            project.course_id = oldstyle_course_id

            current_content_id = project.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = current_content_id.replace("+", "/")
            project.content_id = oldstyle_content_id
            project.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Reviews...')
        workgroup_reviews = WorkgroupReview.objects.all()
        for wr in workgroup_reviews:
            current_content_id = wr.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = current_content_id.replace("+", "/")
            wr.content_id = oldstyle_content_id
            wr.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Peer Reviews...')
        workgroup_peer_reviews = WorkgroupPeerReview.objects.all()
        for wpr in workgroup_reviews:
            current_content_id = wpr.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = current_content_id.replace("+", "/")
            wpr.content_id = oldstyle_content_id
            wpr.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Submission Reviews...')
        workgroup_submission_reviews = WorkgroupSubmissionReview.objects.all()
        for wsr in workgroup_submission_reviews:
            current_content_id = wsr.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = current_content_id.replace("+", "/")
            wsr.content_id = oldstyle_content_id
            wsr.save()
        log.warning('Complete!')
