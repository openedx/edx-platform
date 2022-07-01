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





