"""
Constants for the need of Admin Panel
"""
GROUP_TRAINING_MANAGERS = 'Training Manager'
GROUP_ORGANIZATION_ADMIN = 'Organization Admins'
SELF_ACTIVE_STATUS_CHANGE_ERROR_MSG = "User can't change their own activation status."
ENROLLMENT_COURSE_EXPIRED_MSG = 'Enrollment date is passed for selected courses. ' \
                                'Refresh the page to get the updated course list.'
ENROLLMENT_COURSE_DIFF_ORG_ERROR_MSG = "The user's organization does not match with selected course(s)."
ENROLLMENT_SUCCESS_MESSAGE = 'Enrollment task has been started successfully!\n' \
                             'Please refresh the page after couple of minutes to get the updated stats.'

ORG_ADMIN = 1
STAFF = 2
TRAINING_MANAGER = 3
LEARNER = 4

ORG_ROLES = (
    (ORG_ADMIN, 'Admin'),
    (TRAINING_MANAGER, 'Training Manager'),
    (LEARNER, 'LEARNER'),
)
