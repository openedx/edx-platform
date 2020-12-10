"""
Serializers for applications app
"""
from rest_framework import serializers
from django.utils.translation import ugettext as _

from .helpers import check_validations_for_current_record, check_validations_for_past_record
from .models import Education, WorkExperience


class EducationSerializer(serializers.ModelSerializer):
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
        attrs, errors = self._check_area_of_study_validations(attrs)

        if attrs.get('is_in_progress'):
            errors.update(
                check_validations_for_current_record(
                    attrs, '{key} isn\'t applicable for degree in progress'
                )
            )
        else:
            errors.update(
                check_validations_for_past_record(
                    attrs, '{key} is required for past degree'
                )
            )
        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    def _check_area_of_study_validations(self, attrs):
        """
        Validate area of study by checking if `area_of_study` is provided for all degrees except for
        `high school diploma` and if it isn't raising exception. For `high school diploma` if value of `area_of_study`
        is provided replace it with empty string`''`.

        Arguments:
            attrs (dict): Dictionary containing education attributes

        Returns:
            dicts: Returns updated education attributes and errors if any in dictionary
        """
        errors = {}
        if attrs.get('degree') == 'HD':
            attrs['area_of_study'] = ''
        elif not attrs.get('area_of_study'):
            errors['area_of_study'] = _('Area of study is required for all degrees above High School Diploma')
        return attrs, errors

    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = (
            'id', 'created', 'modified',
        )


class WorkExperienceSerializer(serializers.ModelSerializer):
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
            'id', 'created', 'modified',
        )
