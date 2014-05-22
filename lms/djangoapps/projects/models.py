""" Database ORM models managed by this Django app """

from django.contrib.auth.models import Group, User
from django.db import models
from model_utils.models import TimeStampedModel


class Workgroup(TimeStampedModel):
    """
    Model representing the Workgroup concept.  Workgroups are an
    intersection of Users and CourseContent, although they can also be
    related to other Groups.
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    users = models.ManyToManyField(User, related_name="workgroups")
    groups = models.ManyToManyField(Group, related_name="workgroups")


class Project(TimeStampedModel):
    """
    Model representing the Project concept.  Projects are an
    intersection of Courses, CourseContent, and Workgroups.
    """
    course_id = models.CharField(max_length=255)
    content_id = models.CharField(max_length=255)
    workgroups = models.ManyToManyField(Workgroup, related_name="projects")

    class Meta:
        """ Meta class for defining additional model characteristics """
        unique_together = ("course_id", "content_id")


class Submission(TimeStampedModel):
    """
    Model representing the Submission concept.  A Submission is a project artifact
    created by the Users in a Workgroup.  The document fields are defined by the
    'Group Project' XBlock and data for a specific instance is persisted here
    """
    user = models.ForeignKey(User)
    workgroup = models.ForeignKey(Workgroup, related_name="submissions")
    project = models.ForeignKey(Project, related_name="projects")
    document_id = models.CharField(max_length=255)
    document_url = models.CharField(max_length=255)
    document_mime_type = models.CharField(max_length=255)


class SubmissionReview(TimeStampedModel):
    """
    Model representing the Submission Review concept.  A Submission Review is
    essentially a single question/answer combination for a particular Submission,
    defined in the Group Project XBlock schema.  There can be more than one
    Submission Review for a given Submission.
    """
    submission = models.ForeignKey(Submission, related_name="submission_reviews")
    reviewer = models.ForeignKey(User, related_name="submission_reviews")
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)


class PeerReview(TimeStampedModel):
    """
    Model representing the Peer Review concept.  A Peer Review is a record of a
    specific question/answer defined in the Group Project XBlock schema.  There
    can be more than one Peer Review for a given User.
    """
    user = models.ForeignKey(User, related_name="peer_reviewees")
    reviewer = models.ForeignKey(User, related_name="peer_reviewers")
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
