"""
API Serializers for course waffle flags
"""

from rest_framework import serializers

from cms.djangoapps.contentstore import toggles


class CourseWaffleFlagsSerializer(serializers.Serializer):
    """
    Serializer for course waffle flags
    """
    use_new_home_page = serializers.SerializerMethodField()
    use_new_custom_pages = serializers.SerializerMethodField()
    use_new_schedule_details_page = serializers.SerializerMethodField()
    use_new_advanced_settings_page = serializers.SerializerMethodField()
    use_new_grading_page = serializers.SerializerMethodField()
    use_new_updates_page = serializers.SerializerMethodField()
    use_new_import_page = serializers.SerializerMethodField()
    use_new_export_page = serializers.SerializerMethodField()
    use_new_files_uploads_page = serializers.SerializerMethodField()
    use_new_video_uploads_page = serializers.SerializerMethodField()
    use_new_course_outline_page = serializers.SerializerMethodField()
    use_new_unit_page = serializers.SerializerMethodField()
    use_new_course_team_page = serializers.SerializerMethodField()
    use_new_certificates_page = serializers.SerializerMethodField()
    use_new_textbooks_page = serializers.SerializerMethodField()
    use_new_group_configurations_page = serializers.SerializerMethodField()
    enable_course_optimizer = serializers.SerializerMethodField()

    def get_course_key(self):
        """
        Retrieve the course_key from the context
        """
        return self.context.get("course_key")

    def get_use_new_home_page(self, obj):
        """
        Method to get the use_new_home_page switch
        """
        return toggles.use_new_home_page()

    def get_use_new_custom_pages(self, obj):
        """
        Method to get the use_new_custom_pages switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_custom_pages(course_key)

    def get_use_new_schedule_details_page(self, obj):
        """
        Method to get the use_new_schedule_details_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_schedule_details_page(course_key)

    def get_use_new_advanced_settings_page(self, obj):
        """
        Method to get the use_new_advanced_settings_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_advanced_settings_page(course_key)

    def get_use_new_grading_page(self, obj):
        """
        Method to get the use_new_grading_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_grading_page(course_key)

    def get_use_new_updates_page(self, obj):
        """
        Method to get the use_new_updates_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_updates_page(course_key)

    def get_use_new_import_page(self, obj):
        """
        Method to get the use_new_import_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_import_page(course_key)

    def get_use_new_export_page(self, obj):
        """
        Method to get the use_new_export_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_export_page(course_key)

    def get_use_new_files_uploads_page(self, obj):
        """
        Method to get the use_new_files_uploads_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_files_uploads_page(course_key)

    def get_use_new_video_uploads_page(self, obj):
        """
        Method to get the use_new_video_uploads_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_video_uploads_page(course_key)

    def get_use_new_course_outline_page(self, obj):
        """
        Method to get the use_new_course_outline_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_course_outline_page(course_key)

    def get_use_new_unit_page(self, obj):
        """
        Method to get the use_new_unit_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_unit_page(course_key)

    def get_use_new_course_team_page(self, obj):
        """
        Method to get the use_new_course_team_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_course_team_page(course_key)

    def get_use_new_certificates_page(self, obj):
        """
        Method to get the use_new_certificates_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_certificates_page(course_key)

    def get_use_new_textbooks_page(self, obj):
        """
        Method to get the use_new_textbooks_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_textbooks_page(course_key)

    def get_use_new_group_configurations_page(self, obj):
        """
        Method to get the use_new_group_configurations_page switch
        """
        course_key = self.get_course_key()
        return toggles.use_new_group_configurations_page(course_key)

    def get_enable_course_optimizer(self, obj):
        """
        Method to get the enable_course_optimizer waffle flag
        """
        course_key = self.get_course_key()
        return toggles.enable_course_optimizer(course_key)
