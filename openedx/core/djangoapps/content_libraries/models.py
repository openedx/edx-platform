"""
========================
Content Libraries Models
========================

This module contains the models for new Content Libraries.

LTI 1.3 Models
==============

Content Libraries serves blockstore-based content through LTI 1.3 launches.
The interface supports resource link launches and grading services.  Two use
cases justify the current data model to support LTI launches.  They are:

1. Authentication and authorization.  This use case demands management of user
   lifecycle to authorize access to content and grade submission, and it
   introduces a model to own the authentication business logic related to LTI.

2. Grade and assignments.  When AGS is supported, content libraries store
   additional information concerning the launched resource so that, once the
   grading sub-system submits the score, it can retrieve them to propagate the
   score update into the platform's grade book.

Relationship with LMS's ``lti_provider``` models
------------------------------------------------

The data model above is similar to the one provided by the current LTI 1.1
implementation for modulestore and courseware content.  But, Content Libraries
is orthogonal.  Its use-case is to offer standalone, embedded content from a
specific backend (blockstore).  As such, it decouples from LTI 1.1. and the
logic assume no relationship or impact across the two applications.  The same
reasoning applies to steps beyond the data model, such as at the XBlock
runtime, authentication, and score handling, etc.
"""


import logging
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from opaque_keys.edx.locator import LibraryLocatorV2
from pylti1p3.contrib.django import DjangoDbToolConf
from pylti1p3.contrib.django import DjangoMessageLaunch
from pylti1p3.grade import Grade

from openedx.core.djangoapps.content_libraries.constants import (
    LIBRARY_TYPES, COMPLEX, LICENSE_OPTIONS,
    ALL_RIGHTS_RESERVED,
)
from organizations.models import Organization  # lint-amnesty, pylint: disable=wrong-import-order

from .apps import ContentLibrariesConfig


log = logging.getLogger(__name__)

User = get_user_model()


class ContentLibraryManager(models.Manager):
    """
    Custom manager for ContentLibrary class.
    """
    def get_by_key(self, library_key):
        """
        Get the ContentLibrary for the given LibraryLocatorV2 key.
        """
        assert isinstance(library_key, LibraryLocatorV2)
        return self.get(org__short_name=library_key.org, slug=library_key.slug)


class ContentLibrary(models.Model):
    """
    A Content Library is a collection of content (XBlocks and/or static assets)

    All actual content is stored in Blockstore, and any data that we'd want to
    transfer to another instance if this library were exported and then
    re-imported on another Open edX instance should be kept in Blockstore. This
    model in the LMS should only be used to track settings specific to this Open
    edX instance, like who has permission to edit this content library.
    """
    objects = ContentLibraryManager()

    id = models.AutoField(primary_key=True)
    # Every Library is uniquely and permanently identified by an 'org' and a
    # 'slug' that are set during creation/import. Both will appear in the
    # library's opaque key:
    # e.g. "lib:org:slug" is the opaque key for a library.
    org = models.ForeignKey(Organization, on_delete=models.PROTECT, null=False)
    slug = models.SlugField(allow_unicode=True)
    bundle_uuid = models.UUIDField(unique=True, null=False)
    type = models.CharField(max_length=25, default=COMPLEX, choices=LIBRARY_TYPES)
    license = models.CharField(max_length=25, default=ALL_RIGHTS_RESERVED, choices=LICENSE_OPTIONS)

    # How is this library going to be used?
    allow_public_learning = models.BooleanField(
        default=False,
        help_text=("""
            Allow any user (even unregistered users) to view and interact with
            content in this library (in the LMS; not in Studio). If this is not
            enabled, then the content in this library is not directly accessible
            in the LMS, and learners will only ever see this content if it is
            explicitly added to a course. If in doubt, leave this unchecked.
        """),
    )
    allow_public_read = models.BooleanField(
        default=False,
        help_text=("""
            Allow any user with Studio access to view this library's content in
            Studio, use it in their courses, and copy content out of this
            library. If in doubt, leave this unchecked.
        """),
    )

    class Meta:
        verbose_name_plural = "Content Libraries"
        unique_together = ("org", "slug")

    @property
    def library_key(self):
        """
        Get the LibraryLocatorV2 opaque key for this library
        """
        return LibraryLocatorV2(org=self.org.short_name, slug=self.slug)

    def __str__(self):
        return f"ContentLibrary ({str(self.library_key)})"


class ContentLibraryPermission(models.Model):
    """
    Row recording permissions for a content library
    """
    library = models.ForeignKey(ContentLibrary, on_delete=models.CASCADE, related_name="permission_grants")
    # One of the following must be set (but not both):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)
    # What level of access is granted to the above user or group:
    ADMIN_LEVEL = 'admin'
    AUTHOR_LEVEL = 'author'
    READ_LEVEL = 'read'
    ACCESS_LEVEL_CHOICES = (
        (ADMIN_LEVEL, _("Administer users and author content")),
        (AUTHOR_LEVEL, _("Author content")),
        (READ_LEVEL, _("Read-only")),
    )
    access_level = models.CharField(max_length=30, choices=ACCESS_LEVEL_CHOICES)

    class Meta:
        ordering = ('user__username', 'group__name')
        unique_together = [
            ('library', 'user'),
            ('library', 'group'),
        ]

    def save(self, *args, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ, signature-differs
        """
        Validate any constraints on the model.

        We can remove this and replace it with a proper database constraint
        once we're upgraded to Django 2.2+
        """
        # if both are nonexistent or both are existing, error
        if (not self.user) == (not self.group):
            raise ValidationError(_("One and only one of 'user' and 'group' must be set."))
        return super().save(*args, **kwargs)

    def __str__(self):
        who = self.user.username if self.user else self.group.name
        return f"ContentLibraryPermission ({self.access_level} for {who})"


class LtiProfileManager(models.Manager):
    """
    Custom manager of LtiProfile mode.
    """

    def get_from_claims(self, *, iss, aud, sub):
        """
        Get the an instance from a LTI launch claims.
        """
        return self.get(platform_id=iss, client_id=aud, subject_id=sub)

    def get_or_create_from_claims(self, *, iss, aud, sub):
        """
        Get or create an instance from a LTI launch claims.
        """
        try:
            return self.get_from_claims(iss=iss, aud=aud, sub=sub)
        except self.model.DoesNotExist:
            # User will be created on ``save()``.
            return self.create(platform_id=iss, client_id=aud, subject_id=sub)


class LtiProfile(models.Model):
    """
    Content Librarie LTI's profile for Open edX users.

    Unless Anonymous, this should be a unique representation of the LTI subject
    (as per the client token ``sub`` identify claim) that initiated an LTI
    launch through Content Libraries.
    """

    objects = LtiProfileManager()

    user = models.OneToOneField(
        get_user_model(),
        null=True,
        on_delete=models.CASCADE,
        related_name='contentlibraries_lti_profile',
        verbose_name=_('open edx user'),
    )

    platform_id = models.CharField(
        max_length=255,
        verbose_name=_('platform identifier'),
        help_text=_("The LTI platform identifier to which this profile belongs "
                    "to.")
    )

    client_id = models.CharField(
        max_length=255,
        verbose_name=_('client identifier'),
        help_text=_("The LTI client identifier generated by the platform.")
    )

    subject_id = models.CharField(
        max_length=255,
        verbose_name=_('subject identifier'),
        help_text=_('Identifies the entity that initiated the launch request, '
                    'commonly a user.')
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ['platform_id', 'client_id', 'subject_id']

    @property
    def subject_url(self):
        """
        An local URL that is known to uniquely identify this profile.

        We take advantage of the fact that platform id is required to be an URL
        and append paths with the reamaining keys to it.
        """
        return '/'.join([
            self.platform_id.rstrip('/'),
            self.client_id,
            self.subject_id
        ])

    def save(self, *args, **kwds):
        """
        Get or create an edx user on save.
        """
        if not self.user:
            uid = uuid.uuid5(uuid.NAMESPACE_URL, self.subject_url)
            username = f'urn:openedx:content_libraries:username:{uid}'
            email = f'{uid}@{ContentLibrariesConfig.name}'
            with transaction.atomic():
                if self.user is None:
                    self.user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': email})
                    if created:
                        # LTI users can only auth throught LTI launches.
                        self.user.set_unusable_password()
                    self.user.save()
                super().save(*args, **kwds)

    def __str__(self):
        return self.subject_id


class LtiGradedResourceManager(models.Manager):
    """
    A custom manager for the graded resources model.
    """

    def upsert_from_ags_launch(self, user, block, resource_endpoint, resource_link):
        """
        Update or create a graded resource at AGS launch.
        """
        resource_id = resource_link['id']
        resource_title = resource_link.get('title') or None
        lineitem = resource_endpoint['lineitem']
        lti_profile = user.contentlibraries_lti_profile
        try:
            resource = self.get(
                profile=lti_profile,
                usage_key=block.scope_ids.usage_id
            )
        except self.model.DoesNotExist:
            resource = self.model(
                profile=lti_profile,
                usage_key=block.scope_ids.usage_id,
            )
        resource.resource_title = resource_title
        resource.resource_id = resource_id
        resource.ags_lineitem = lineitem
        resource.save()
        return resource

    def get_from_user_id(self, user_id, **kwds):
        """
        Retrieve a resource for a given user id holding an lti profile.
        """
        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist as exc:
            raise self.model.DoesNotExist('User specified was not found.') from exc
        profile = getattr(user, 'contentlibraries_lti_profile', None)
        if not profile:
            raise self.model.DoesNotExist('User does not have a LTI profile.')
        kwds['profile'] = profile
        return self.get(**kwds)


class LtiGradedResource(models.Model):
    """
    A content libraries resource launched through LTI with AGS enabled.

    Essentially, an instance of this model represents a successful LTI AGS
    launch.  This model links the profile that launched the resource with the
    resource itself, allowing identifcation of the link through its usage key
    string and user id.
    """

    objects = LtiGradedResourceManager()

    profile = models.ForeignKey(
        LtiProfile,
        on_delete=models.CASCADE,
        related_name='lti_resources',
        help_text=_('The authorized LTI profile that launched the resource.'))

    usage_key = models.CharField(
        max_length=255,
        help_text=_('The usage key string of the blockstore resource serving the '
                    'content of this launch.'),
    )

    resource_id = models.CharField(
        max_length=255,
        help_text=_('The platform unique identifier of this resource in the '
                    'platform, also known as "resource link id".'),
    )

    resource_title = models.CharField(
        max_length=255,
        null=True,
        help_text=_('The platform descriptive title for this resource placed in '
                    'the platform.'),
    )

    ags_lineitem = models.CharField(
        max_length=255,
        null=False,
        help_text=_('If AGS was enabled during launch, this should hold the '
                    'lineitem ID.'))

    class Meta:
        unique_together = (['usage_key', 'profile'])

    def update_score(self, weighted_earned, weighted_possible, timestamp):
        """
        Use LTI's score service to update the platform's gradebook.

        This method synchronously send a request to the platform to update the
        assignment score, raising in case the
        """

        launch_data = {
            'iss': self.profile.platform_id,
            'aud': self.profile.client_id,
            'https://purl.imsglobal.org/spec/lti-ags/claim/endpoint': {
                'lineitem': self.ags_lineitem,
                'scope': {
                    'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem',
                    'https://purl.imsglobal.org/spec/lti-ags/scope/score',
                }
            }
        }

        tool_config = DjangoDbToolConf()

        ags = (
            DjangoMessageLaunch(request=None, tool_config=tool_config)
            .set_auto_validation(enable=False)
            .set_jwt({'body': launch_data})
            .set_restored()
            .validate_registration()
            .get_ags()
        )

        if weighted_possible == 0:
            weighted_score = 0
        else:
            weighted_score = float(weighted_earned) / float(weighted_possible)

        ags.put_grade(
            Grade()
            .set_score_given(weighted_score)
            .set_score_maximum(1)
            .set_timestamp(timestamp.isoformat())
            .set_activity_progress('Submitted')
            .set_grading_progress('FullyGraded')
            .set_user_id(self.profile.subject_id)
        )

    def __str__(self):
        return self.usage_key
