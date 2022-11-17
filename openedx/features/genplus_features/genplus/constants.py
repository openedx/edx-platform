class GenUserRoles:
    """
    Role of a genplus user coming from RMUnify
    """
    STUDENT = 'Student'
    FACULTY = 'Faculty'
    AFFILIATE = 'Affiliate'
    EMPLOYEE = 'Employee'
    TEACHING_STAFF = 'TeachingStaff'
    NON_TEACHING_STAFF = 'NonTeachingStaff'

    __ALL__ = (STUDENT, FACULTY, AFFILIATE, EMPLOYEE, TEACHING_STAFF, NON_TEACHING_STAFF)
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )


class ClassColors:

    """
    color choices for the classes
    """
    RED = '#E53935'
    LIME = '#AEEA00'
    ORANGE = '#EF6C00'
    INDIGO = '#304FFE'
    CYAN = '#0097A7'
    BLUE = '#1E88E5'
    GREEN = '#388E3C'

    __ALL__ = (RED, LIME, ORANGE, INDIGO, CYAN, BLUE, GREEN)
    __MODEL_CHOICES__ = (
        (color, color) for color in __ALL__
    )


class JournalTypes:

    """
    Journal choices for the classes
    """
    TEACHER_FEEDBACK = 'TeacherFeedback'
    STUDENT_POST = 'StudentReflection'

    __ALL__ = (TEACHER_FEEDBACK, STUDENT_POST)
    __MODEL_CHOICES__ = (
        (journal_type, journal_type) for journal_type in __ALL__
    )


class SchoolTypes:

    """
    school types choices for the classes
    """
    RM_UNIFY = 'RmUnify'
    PRIVATE = 'Private'

    __ALL__ = (RM_UNIFY, PRIVATE)
    __MODEL_CHOICES__ = (
        (school_type, school_type) for school_type in __ALL__
    )


class ClassTypes:

    """
    class types choices for the classes
    """
    TEACHING_GROUP = 'TeachingGroup'
    REGISTRATION_GROUP = 'RegistrationGroup'

    __ALL__ = (TEACHING_GROUP, REGISTRATION_GROUP)
    __MODEL_CHOICES__ = (
        (class_type, class_type) for class_type in __ALL__
    )

class ActivityTypes:

    """
    Activity choices
    """
    JOURNAL_ENTRY_BY_STUDENT = 'JournalEntryByStudent'
    JOURNAL_ENTRY_BY_TEACHER = 'JournalEntryByTeacher'
    BADGE_AWARD = 'BadgeAward'
    LESSON_COMPLETION = 'LessonCompletion'
    ON_BOARDED = 'OnBoarded'

    __ALL__ = (JOURNAL_ENTRY_BY_STUDENT, JOURNAL_ENTRY_BY_TEACHER, BADGE_AWARD, LESSON_COMPLETION, ON_BOARDED)
    __MODEL_CHOICES__ = (
        (activity_type, activity_type) for activity_type in __ALL__
    )


class EmailTypes:

    """
    Email type choices
    """
    MISSING_CLASS_EMAIL= 'Missing Class'

    __ALL__ = (MISSING_CLASS_EMAIL,)
    __MODEL_CHOICES__ = (
        (email_type, email_type) for email_type in __ALL__
    )
