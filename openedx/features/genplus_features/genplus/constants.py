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
