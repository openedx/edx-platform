"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from projects.models import Project, WorkgroupReview, WorkgroupPeerReview, WorkgroupSubmissionReview

log = logging.getLogger(__name__)


def _migrate_course_id(old_course_id):
    course_id = old_course_id.replace("slashes:", "")
    course_id = course_id.replace("course-v1:", "")
    course_id = course_id.replace("+", "/")
    return course_id


def _migrate_content_id(old_content_id):
    if "slashes:" in old_content_id or "course-v1:" in old_content_id:
        new_content_id = self._migrate_course_id(old_content_id)
    else:
        content_id = old_content_id.replace("location:", "")
        content_components = content_id.split('+')
        new_content_id = "i4x:/"
        for x in range(0, len(content_components)):
            if x != 2:
                new_content_id = "{}/{}".format(new_content_id, content_components[x])
    return new_content_id


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):

        log.warning('Migrating Projects...')
        projects = Project.objects.all()
        for project in projects:
            project.course_id = _migrate_course_id(project.course_id)
            project.content_id = _migrate_content_id(project.content_id)
            project.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Reviews...')
        workgroup_reviews = WorkgroupReview.objects.all()
        for wr in workgroup_reviews:
            if wr.content_id is not None:
                wr.content_id = _migrate_content_id(wr.content_id)
                wr.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Peer Reviews...')
        workgroup_peer_reviews = WorkgroupPeerReview.objects.all()
        for wpr in workgroup_peer_reviews:
            if wpr.content_id is not None:
                wpr.content_id = _migrate_content_id(wpr.content_id)
                wpr.save()
        log.warning('Complete!')

        log.warning('Migrating Workgroup Submission Reviews...')
        workgroup_submission_reviews = WorkgroupSubmissionReview.objects.all()
        for wsr in workgroup_submission_reviews:
            if wsr.content_id is not None:
                wsr.content_id = _migrate_content_id(wsr.content_id)
                wsr.save()
        log.warning('Complete!')
