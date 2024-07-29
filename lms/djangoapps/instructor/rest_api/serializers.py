from rest_framework import serializers



"""
Example usage
serializer = ProblemResponseRequestSerializer(data=request.data)
if serializer.is_valid():
    # Access validated data with serializer.validated_data
else:
    # Handle invalid data with serializer.errors

"""
class ProblemResponseRequestSerializer(serializers.Serializer):
    problem_location = serializers.CharField(required=True)
    problem_types_filter = serializers.CharField(required=False, allow_blank=True)
    
    def validate_problem_location(self, value):
        locations = value.split(',')
        if not all(locations):
            raise serializers.ValidationError("All problem locations must be valid non-empty strings.")
        return locations
    
    def validate_problem_types_filter(self, value):
        if value:
            types = value.split(',')
            if not all(types):
                raise serializers.ValidationError("All problem types must be valid non-empty strings.")
            return types
        return []