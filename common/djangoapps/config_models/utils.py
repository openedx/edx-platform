"""
Utilities for working with ConfigurationModels.
"""
from django.apps import apps
from rest_framework.parsers import JSONParser
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User


def get_serializer_class(configuration_model):
    """ Returns a ConfigurationModel serializer class for the supplied configuration_model. """
    class AutoConfigModelSerializer(ModelSerializer):
        """Serializer class for configuration models."""

        class Meta(object):
            """Meta information for AutoConfigModelSerializer."""
            model = configuration_model

        def create(self, validated_data):
            if "changed_by_username" in self.context:
                validated_data['changed_by'] = User.objects.get(username=self.context["changed_by_username"])
            return super(AutoConfigModelSerializer, self).create(validated_data)

    return AutoConfigModelSerializer


def deserialize_json(stream, username):
    """
    Given a stream containing JSON, deserializers the JSON into ConfigurationModel instances.

    The stream is expected to be in the following format:
        { "model": "config_models.ExampleConfigurationModel",
          "data":
            [
              { "enabled": True,
                "color": "black"
                ...
              },
              { "enabled": False,
                "color": "yellow"
                ...
              },
              ...
            ]
        }

    If the provided stream does not contain valid JSON for the ConfigurationModel specified,
    an Exception will be raised.

    Arguments:
            stream: The stream of JSON, as described above.
            username: The username of the user making the change. This must match an existing user.

    Returns: the number of created entries
    """
    parsed_json = JSONParser().parse(stream)
    serializer_class = get_serializer_class(apps.get_model(parsed_json["model"]))
    list_serializer = serializer_class(data=parsed_json["data"], context={"changed_by_username": username}, many=True)
    if list_serializer.is_valid():
        model_class = serializer_class.Meta.model
        for data in reversed(list_serializer.validated_data):
            if model_class.equal_to_current(data):
                list_serializer.validated_data.remove(data)

        entries_created = len(list_serializer.validated_data)
        list_serializer.save()
        return entries_created
    else:
        raise Exception(list_serializer.error_messages)
