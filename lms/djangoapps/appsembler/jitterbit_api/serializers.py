# """
# Django REST Framework serializers for the User API application
# """
# from django.contrib.auth.models import User
# from rest_framework import serializers
# from student.models import UserProfile

# # from .models import UserPreference
# class UserListSerializer()


# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     """
#     Serializer that generates a representation of a User entity containing a subset of fields
#     """
#     name = serializers.SerializerMethodField()
#     preferences = serializers.SerializerMethodField()

#     def get_name(self, user):
#         """
#         Return the name attribute from the user profile object
#         """
#         profile = UserProfile.objects.get(user=user)
#         return profile.name

#     def get_preferences(self, user):
#         """
#         Returns the set of preferences as a dict for the specified user
#         """
#         return dict([(pref.key, pref.value) for pref in user.preferences.all()])

#     class Meta(object):
#         model = User
#         # This list is the minimal set required by the notification service
#         fields = ("id", "url", "email", "name", "username", "preferences")
#         read_only_fields = ("id", "email", "username")

