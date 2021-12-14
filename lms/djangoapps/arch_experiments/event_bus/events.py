course_event_key_schema = """
    {
        "namespace": "djangoapps.arch_experiments.event_bus",
        "name": "CourseEventKey",
        "type": "record",
        "fields": [
            {"name": "course_key", "type": "string"}
        ]
    }
"""

class CourseEventKey:
    def __init__(self, key):
        self.course_key = key

    @staticmethod
    def from_dict(obj, ctx):
        return CourseEventKey(obj['course_key'])

    @staticmethod
    def to_dict(course_event_key, ctx):
        return { "course_key": course_event_key.course_key }

course_schema = """
    {
        "namespace":"djangoapps.arch_experiments.event_bus",
        "name": "Course",
        "type": "record",
        "fields": [
            {"name":"course_key", "type":"string"},
            {"name":"title", "type":"string"},
            {"name":"organization","type":"string"}
        ]
    }
"""

course_event_value_schema = """
    {
        "namespace": "djangoapps.arch_experiments.event_bus",
        "name": "CourseEnrollmentEventValue",
        "type": "record",
        "fields": [
            {
                "name":"course", 
                "type": {
                    "type":"record",
                    "name":"Course",
                    "fields": [
                        {"name":"course_key", "type":"string"},
                        {"name":"title", "type":"string"},
                        {"name":"organization","type":"string"}
                    ]
                }
            },
            {"name": "user_id", "type": "string"},
            {"name": "is_enroll", "type": "boolean"}
        ]
    }
"""

class Course:
    def __init__(self, course_key, title, org):
        self.course_key = course_key
        self.title = title
        self.organization = org

    def formatted_title(self):
        return f"{self.title} from {self.organization}"

class CourseEnrollmentEventValue:
    def __init__(self, course, user_id, is_enroll):
        self.course = course
        self.user_id = user_id
        self.is_enroll = is_enroll

    @staticmethod
    def from_dict(obj, ctx=None):
        return CourseEnrollmentEventValue(
            Course(obj['course']['course_key'], obj['course']['title'], obj['course']['organization']),
            obj['user_id'],
            obj['is_enroll']
        )

    @staticmethod
    def to_dict(course_enrollment, ctx=None):
        return {
            "course": {
                "title": course_enrollment.course.title,
                "course_key": course_enrollment.course.course_key,
                "organization": course_enrollment.course.organization,
            },
            "user_id": course_enrollment.user_id,
            "is_enroll": course_enrollment.is_enroll,
        }


class LicenseTrackingEvent:

    def __init__(self, **kwargs):
        self.license_uuid = kwargs.get('license_uuid','')
        self.license_activation_key = kwargs.get('license_activation_key','')
        self.previous_license_uuid = kwargs.get('previous_license_uuid','')
        self.assigned_date = kwargs.get('assigned_date','')
        self.activation_date = kwargs.get('activation_date', '')
        self.assigned_lms_user_id = kwargs.get('assigned_lms_user_id','')
        self.assigned_email = kwargs.get('assigned_email','')
        self.expiration_processed = kwargs.get('expiration_processed','')
        self.auto_applied = kwargs.get('auto_applied','')
        self.enterprise_customer_uuid = kwargs.get('enterprise_customer_uuid', None)
        self.enterprise_customer_slug = kwargs.get('enterprise_customer_slug', None)
        self.enterprise_customer_name = kwargs.get('enterprise_customer_name', None)
        self.customer_agreement_uuid = kwargs.get('customer_agreement_uuid', None)

    LICENSE_TRACKING_EVENT_AVRO_SCHEMA = """
        {
            "namespace": "license_manager.apps.subscriptions",
            "name": "TrackingEvent",
            "type": "record",
            "fields": [
                {"name": "license_uuid", "type": "string"},
                {"name": "license_activation_key", "type": "string"},
                {"name": "previous_license_uuid", "type": "string"},
                {"name": "assigned_date", "type": "string"},
                {"name": "assigned_lms_user_id", "type": "string"},
                {"name": "assigned_email", "type":"string"},
                {"name": "expiration_processed", "type": "boolean"},
                {"name": "auto_applied", "type": "boolean", "default": "false"},
                {"name": "enterprise_customer_uuid", "type": ["string", "null"], "default": "null"},
                {"name": "customer_agreement_uuid", "type": ["string", "null"], "default": "null"},
                {"name": "enterprise_customer_slug", "type": ["string", "null"], "default": "null"},
                {"name": "enterprise_customer_name", "type": ["string", "null"], "default": "null"}
            ]
        }

    """

    @staticmethod
    def from_dict(dict, ctx):
        return LicenseTrackingEvent(**dict)

    @staticmethod
    def to_dict(obj, ctx=None):
        return {
            'enterprise_customer_uuid': obj.enterprise_customer_uuid,
            'customer_agreement_uuid': obj.customer_agreement_uuid,
            'enterprise_customer_slug': obj.enterprise_customer_slug,
            'enterprise_customer_name': obj.enterprise_customer_name,
            "license_uuid": obj.license_uuid,
            "license_activation_key": obj.license_activation_key,
            "previous_license_uuid": obj.previous_license_uuid,
            "assigned_date": obj.assigned_date,
            "activation_date": obj.activation_date,
            "assigned_lms_user_id": (obj.assigned_lms_user_id or ''),
            "assigned_email": (obj.assigned_email or ''),
            "expiration_processed": obj.expiration_processed,
            "auto_applied": (obj.auto_applied or False),
        }
