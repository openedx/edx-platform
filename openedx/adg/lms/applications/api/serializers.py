"""
Serializers for applications app
"""
from rest_framework import serializers

from openedx.adg.lms.applications.constants import MAX_NUMBER_OF_REFERENCES, MAX_REFERENCE_ERROR_MSG
from openedx.adg.lms.applications.helpers import check_validations_for_current_record, check_validations_for_past_record
from openedx.adg.lms.applications.models import Education, Reference, WorkExperience


class ApplicationRequirementsSerializer(serializers.ModelSerializer):
    """
    Base serializer to add `user_application` while validating the data for Education, Work Experience and References
    while creating and updating objects.
    """

    def validate(self, attrs):
        """
        Adds `user_application` to the data using the `request.user`.

        Args:
            attrs (dict): Dict containing data to be validated

        Returns:
            dict: Validated data
        """
        user = self.context['request'].user

        if hasattr(user, 'application'):
            attrs['user_application'] = user.application
        else:
            raise serializers.ValidationError('User has no written application')
        return super(ApplicationRequirementsSerializer, self).validate(attrs)


class EducationSerializer(ApplicationRequirementsSerializer):
    """
    Serializer for the `Education` model
    """

    def validate(self, attrs):
        """
        Custom validations on education attrs

        Arguments:
            attrs (dict): Dictionary containing education attributes

        Returns:
            dict: Returns updated education attributes after validation or raises validation exceptions
        """
        attrs = self._check_area_of_study_validations(attrs)
        if attrs.get('is_in_progress'):
            errors = check_validations_for_current_record(attrs, '{key} isn\'t applicable for degree in progress')
        else:
            errors = check_validations_for_past_record(attrs, '{key} is required for past degree')
        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    def _check_area_of_study_validations(self, attrs):
        """
        Validate area of study by checking if `area_of_study` is provided for `high school diploma` and
        replace it with empty string `''`.

        Arguments:
            attrs (dict): Dictionary containing education attributes

        Returns:
            dicts: Returns updated education attributes and errors if any in dictionary
        """
        if attrs.get('degree') == Education.HIGH_SCHOOL_DIPLOMA:
            attrs['area_of_study'] = ''
        return attrs

    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = (
            'id', 'created', 'modified', 'user_application',
        )


class WorkExperienceSerializer(ApplicationRequirementsSerializer):
    """
    Serializer for the `WorkExperience` model
    """

    def validate(self, attrs):
        """
        Custom validations on work experience attrs

        Arguments:
            attrs (dict): Dictionary containing work experience attributes

        Returns:
            dict: Returns updated work experience attributes after validation or raises validation exceptions
        """
        if attrs.get('is_current_position'):
            errors = check_validations_for_current_record(
                attrs, '{key} isn\'t applicable for current work experience'
            )
        else:
            errors = check_validations_for_past_record(
                attrs, '{key} is required for past work experience'
            )
        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    class Meta:
        model = WorkExperience
        fields = '__all__'
        read_only_fields = (
            'id', 'created', 'modified', 'user_application',
        )


class ReferenceSerializer(ApplicationRequirementsSerializer):
    """
    Serializer for the `Reference` model
    """

    def validate(self, attrs):
        """
        Validate that max reference limit against a user application is not exceeded in case of a create request
        """
        super().validate(attrs)

        is_update_request = bool(self.instance)
        if is_update_request:
            return attrs

        existing_reference_count = Reference.objects.filter(user_application=attrs['user_application']).count()
        if existing_reference_count == MAX_NUMBER_OF_REFERENCES:
            raise serializers.ValidationError({'user_application': MAX_REFERENCE_ERROR_MSG})

        return attrs

    class Meta:
        model = Reference
        fields = ['id', 'name', 'position', 'relationship', 'phone_number', 'email', 'user_application']
        read_only_fields = ('user_application',)
