from rest_framework import serializers

from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import UsageKey

from .constants import INVALID_PROBLEM_ID_MSG
from .models import CompetencyAssessmentRecord


class CompetencyAssessmentRecordSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_problem_id(self, problem_id):
        """
        validate if problem_id is valid UsageKeyField or not
        """
        try:
            return UsageKey.from_string(problem_id)
        except InvalidKeyError:
            raise serializers.ValidationError(INVALID_PROBLEM_ID_MSG)

    class Meta:
        model = CompetencyAssessmentRecord
        fields = '__all__'
