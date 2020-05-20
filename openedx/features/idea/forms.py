# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import CharField, ModelForm, Textarea, TextInput
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.onboarding.helpers import COUNTRIES, get_country_iso
from lms.djangoapps.onboarding.models import Organization
from openedx.features.philu_utils.utils import validate_file_size

from .constants import IDEA_FILE_MAX_SIZE, IDEA_IMAGE_MAX_SIZE, ORGANIZATION_NAME_MAX_LENGTH
from .helpers import validate_image_dimensions
from .models import Idea


class IdeaCreationForm(ModelForm):
    """
    A model form to create new Idea. Separate fields for organization_name is used
    to make model field organization work with custom widget on frontend.
    """

    prefix = 'idea'
    label_suffix = ''

    organization_name = CharField(
        max_length=ORGANIZATION_NAME_MAX_LENGTH,
        label=_('Organization Name*'),
        required=True,
        widget=TextInput(),
    )

    class Meta:
        model = Idea
        exclude = ('user', 'favorites', 'organization',)

        labels = {
            'city': 'City:',
            'country': 'Country:',
            'description': 'Idea Description*',
            'organization_mission': 'Organization Mission*',
            'overview': 'Idea Overview*',
            'title': 'Idea Title*',
        }

        widgets = {
            'overview': Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super(IdeaCreationForm, self).__init__(*args, **kwargs)
        self.label_suffix = ''

        initial_arguments = kwargs.get('initial', {})
        self.user = initial_arguments.get('user', None)
        self.disable_field('organization_name', initial_arguments)
        self.disable_field('country', initial_arguments)
        self.disable_field('city', initial_arguments)

        self.fields['image'].widget.attrs.update(
            {'accept': 'image/jpg, image/png', 'data-max-size': IDEA_IMAGE_MAX_SIZE})
        self.fields['file'].widget.attrs.update(
            {'accept': '.docx, .pdf, .txt', 'data-max-size': IDEA_FILE_MAX_SIZE})

    def disable_field(self, field_name, initial_arguments):
        initial_field_arguments = initial_arguments.get(field_name, None)
        # django will save initial values even if disabled fields are tampered with
        self.fields[field_name].disabled = True if initial_field_arguments else False

    def clean_image(self):
        image = self.cleaned_data['image']
        validate_image_dimensions(image)
        validate_file_size(image, max_allowed_size=IDEA_IMAGE_MAX_SIZE)
        return image

    def clean_file(self):
        idea_file = self.cleaned_data['file']
        validate_file_size(idea_file, max_allowed_size=IDEA_FILE_MAX_SIZE)
        return idea_file

    def save(self, commit=True):
        idea = super(IdeaCreationForm, self).save(commit=False)

        idea.user = self.user

        organization_name = self.cleaned_data.get('organization_name')
        organization = Organization.objects.filter(label__iexact=organization_name).first()

        if not organization:
            organization = Organization(label=organization_name)

        idea.country = self.cleaned_data.get('country')

        is_userprofile_updated = False
        userprofile = idea.user.profile
        if not userprofile.country:
            userprofile.country = idea.country
            is_userprofile_updated = True

        if not userprofile.city:
            userprofile.city = idea.city
            is_userprofile_updated = True

        if not commit:
            idea.organization = organization
            return idea

        with transaction.atomic():
            # Prevent inconsistent database entries and rollback everything, if any exception
            # occurs while saving data to organization, extended profile, userprofile or idea
            organization.save()

            extended_profile = idea.user.extended_profile
            if not extended_profile.organization:
                extended_profile.organization = organization
                extended_profile.is_first_learner = organization.can_join_as_first_learner(
                    exclude_user=idea.user)
                extended_profile.save()

            if is_userprofile_updated:
                userprofile.save()

            idea.organization = organization
            idea.save()

        return idea
