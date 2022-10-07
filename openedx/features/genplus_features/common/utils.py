from rest_framework import serializers


def get_generic_serializer(model_arg, depth_arg=1):
    class GenericSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_arg
            fields = '__all__'
            depth = depth_arg

    return GenericSerializer
