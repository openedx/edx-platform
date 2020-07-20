from rest_framework import serializers

from .helpers import validate_problem_id
from .models import CompetencyAssessmentRecord


class CompetencyAssessmentRecordSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_problem_id(self, problem_id):
        """
        validate if problem_id is valid UsageKeyField or not
        """
        return validate_problem_id(problem_id)

    class Meta:
        model = CompetencyAssessmentRecord
        fields = '__all__'
