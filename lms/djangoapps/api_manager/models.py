# pylint: disable=E1101

""" Database ORM models managed by this Django app """

from django.contrib.auth.models import Group, User
from django.db import models

from model_utils.models import TimeStampedModel
from .utils import is_int

from projects.models import Workgroup


class GroupRelationship(TimeStampedModel):
    """
    The GroupRelationship model contains information describing the relationships of a group,
    which allows us to utilize Django's user/group/permission
    models and features instead of rolling our own.
    """
    group = models.OneToOneField(Group, primary_key=True)
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self',
                                     related_name="child_groups",
                                     blank=True, null=True, default=0)
    linked_groups = models.ManyToManyField('self',
                                           through="LinkedGroupRelationship",
                                           symmetrical=False,
                                           related_name="linked_to+"),
    record_active = models.BooleanField(default=True)

    def add_linked_group_relationship(self, to_group_relationship, symmetrical=True):
        """ Create a new group-group relationship """
        relationship = LinkedGroupRelationship.objects.get_or_create(
            from_group_relationship=self,
            to_group_relationship=to_group_relationship)
        if symmetrical:
            # avoid recursion by passing `symm=False`
            to_group_relationship.add_linked_group_relationship(self, False)
        return relationship

    def remove_linked_group_relationship(self, to_group_relationship, symmetrical=True):
        """ Remove an existing group-group relationship """
        LinkedGroupRelationship.objects.filter(
            from_group_relationship=self,
            to_group_relationship=to_group_relationship).delete()
        if symmetrical:
            # avoid recursion by passing `symm=False`
            to_group_relationship.remove_linked_group_relationship(self, False)
        return

    def get_linked_group_relationships(self):
        """ Retrieve an existing group-group relationship """
        efferent_relationships = LinkedGroupRelationship.objects.filter(from_group_relationship=self)
        matching_relationships = efferent_relationships
        return matching_relationships

    def check_linked_group_relationship(self, relationship_to_check, symmetrical=False):
        """ Confirm the existence of a possibly-existing group-group relationship """
        query = dict(
            to_group_relationships__from_group_relationship=self,
            to_group_relationships__to_group_relationship=relationship_to_check,
        )
        if symmetrical:
            query.update(
                from_group_relationships__to_group_relationship=self,
                from_group_relationships__from_group_relationship=relationship_to_check,
            )
        return GroupRelationship.objects.filter(**query).exists()


class LinkedGroupRelationship(TimeStampedModel):
    """
    The LinkedGroupRelationship model manages self-referential two-way
    relationships between group entities via the GroupRelationship model.
    Specifying the intermediary table allows for the definition of additional
    relationship information
    """
    from_group_relationship = models.ForeignKey(GroupRelationship,
                                                related_name="from_group_relationships",
                                                verbose_name="From Group")
    to_group_relationship = models.ForeignKey(GroupRelationship,
                                              related_name="to_group_relationships",
                                              verbose_name="To Group")
    record_active = models.BooleanField(default=True)


class CourseGroupRelationship(TimeStampedModel):
    """
    The CourseGroupRelationship model contains information describing the
    link between a course and a group.  A typical use case for this table
    is to manage the courses for an XSeries or other sort of program.
    """
    course_id = models.CharField(max_length=255, db_index=True)
    group = models.ForeignKey(Group, db_index=True)
    record_active = models.BooleanField(default=True)


class GroupProfile(TimeStampedModel):
    """
    This table will provide additional tables regarding groups. This has a foreign key to
    the auth_groups table
    """

    class Meta:
        """
        Meta class for modifying things like table name
        """
        db_table = "auth_groupprofile"

    group = models.OneToOneField(Group, db_index=True)
    group_type = models.CharField(null=True, max_length=32, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    data = models.TextField(blank=True)  # JSON dictionary for generic key/value pairs
    record_active = models.BooleanField(default=True)


class CourseContentGroupRelationship(TimeStampedModel):
    """
    The CourseContentGroupRelationship model contains information describing the
    link between a particular courseware element (chapter, unit, video, etc.)
    and a group.  A typical use case for this table is to support the concept
    of a student workgroup for a given course, where the project is actually
    a Chapter courseware element.
    """
    course_id = models.CharField(max_length=255, db_index=True)
    content_id = models.CharField(max_length=255, db_index=True)
    group_profile = models.ForeignKey(GroupProfile, db_index=True)
    record_active = models.BooleanField(default=True)

    class Meta:
        """
        Mapping model to enable grouping of course content such as chapters
        """
        unique_together = ("course_id", "content_id", "group_profile")


class Organization(TimeStampedModel):
    """
    Main table representing the Organization concept.  Organizations are
    primarily a collection of Users.
    """
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.EmailField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    workgroups = models.ManyToManyField(Workgroup, related_name="organizations")
    users = models.ManyToManyField(User, related_name="organizations")
    groups = models.ManyToManyField(Group, related_name="organizations")


class CourseModuleCompletion(TimeStampedModel):
    """
    The CourseModuleCompletion model contains user, course, module information
    to monitor a user's progression throughout the duration of a course,
    we need to observe and record completions of the individual course modules.
    """
    user = models.ForeignKey(User, db_index=True, related_name="course_completions")
    course_id = models.CharField(max_length=255, db_index=True)
    content_id = models.CharField(max_length=255, db_index=True)
    stage = models.CharField(max_length=255, null=True, blank=True)


class APIUserQuerySet(models.query.QuerySet):  # pylint: disable=R0924
    """ Custom QuerySet to modify id based lookup """
    def filter(self, *args, **kwargs):
        if 'id' in kwargs and not is_int(kwargs['id']):
            kwargs['anonymoususerid__anonymous_user_id'] = kwargs['id']
            del kwargs['id']
        return super(APIUserQuerySet, self).filter(*args, **kwargs)


class APIUserManager(models.Manager):
    """ Custom Manager """
    def get_query_set(self):
        return APIUserQuerySet(self.model)


class APIUser(User):
    """
    A proxy model for django's auth.User to add AnonymousUserId fallback
    support in User lookups
    """
    objects = APIUserManager()

    class Meta:
        """ Meta attribute to make this a proxy model"""
        proxy = True
