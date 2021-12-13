""" Error codes and exceptions for ESG """

# Catch-all error if we don't supply anything
ERR_UNKNOWN = "ERR_UNKNOWN"

# A request is missing a required query param
ERR_MISSING_PARAM = "ERR_MISSING_PARAM"

# The requested ORA_LOCATION could not be found in the course
ERR_BAD_ORA_LOCATION = "ERR_BAD_ORA_LOCATION"

# User tried to operate on a submission that they do not have a lock for
ERR_LOCK_CONTESTED = "ERR_LOCK_CONTESTED"


class ErrorSerializer(serializers.Serializer):
    """ Returns error code and unpacks additional context """
    error = serializers.CharField(default=ERR_UNKNOWN)

    def to_representation(self, instance):
        """ Override to unpack context alongside error code """
        output = super().to_representation(instance)
        for key, value in self.context.items():
            output[key] = value

        return output

