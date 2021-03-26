""" CCX API v0 Serializers. """


from ccx_keys.locator import CCXLocator
from rest_framework import serializers

from lms.djangoapps.ccx.models import CustomCourseForEdX


class CCXCourseSerializer(serializers.ModelSerializer):
    """
    Serializer for CCX courses
    """
    ccx_course_id = serializers.SerializerMethodField()
    master_course_id = serializers.CharField(source='course_id')
    display_name = serializers.CharField()
    coach_email = serializers.EmailField(source='coach.email')
    start = serializers.CharField(allow_blank=True)
    due = serializers.CharField(allow_blank=True)
    max_students_allowed = serializers.IntegerField(source='max_student_enrollments_allowed')
    course_modules = serializers.SerializerMethodField()

    class Meta:
        model = CustomCourseForEdX
        fields = (
            "ccx_course_id",
            "master_course_id",
            "display_name",
            "coach_email",
            "start",
            "due",
            "max_students_allowed",
            "course_modules",
        )
        read_only_fields = (
            "ccx_course_id",
            "master_course_id",
            "start",
            "due",
        )

    @staticmethod
    def get_ccx_course_id(obj):
        """
        Getter for the CCX Course ID
        """
        return str(CCXLocator.from_course_locator(obj.course.id, obj.id))

    @staticmethod
    def get_course_modules(obj):
        """
        Getter for the Course Modules. The list is stored in a compressed field.
        """
        return obj.structure or []
