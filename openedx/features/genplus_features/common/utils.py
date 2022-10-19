from rest_framework import serializers


def get_generic_serializer(model_args, depth_arg=1):
    class GenericSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_args['name']
            fields = model_args['fields']
            depth = depth_arg

    return GenericSerializer
