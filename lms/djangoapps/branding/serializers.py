"""
Serializers for the branding app.
"""

from rest_framework import serializers

import lms.djangoapps.branding.toggles as branding_toggles


class WaffleFlagsSerializer(serializers.Serializer):
    """
    Serializer for waffle flags.
    """
    use_new_index_page = serializers.SerializerMethodField()
    use_new_catalog_page = serializers.SerializerMethodField()
    use_new_course_about_page = serializers.SerializerMethodField()

    def get_course_key(self):
        """
        Retrieve the course_key from the context.
        """
        return self.context.get("course_key")

    def get_use_new_index_page(self, obj):
        """
        Returns whether the new index page is enabled.
        """
        course_key = self.get_course_key()
        return branding_toggles.use_new_index_page(course_key)

    def get_use_new_catalog_page(self, obj):
        """
        Returns whether the new catalog page is enabled.
        """
        course_key = self.get_course_key()
        return branding_toggles.use_new_catalog_page(course_key)

    def get_use_new_course_about_page(self, obj):
        """
        Returns whether the new course about page is enabled.
        """
        course_key = self.get_course_key()
        return branding_toggles.use_new_course_about_page(course_key)
