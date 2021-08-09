"""
Constants for the need of Admin Panel
"""
GROUP_TRAINING_MANAGERS = 'Training Manager'
GROUP_ORGANIZATION_ADMIN = 'Organization Admins'
SELF_ACTIVE_STATUS_CHANGE_ERROR_MSG = "User can't change their own activation status."
ORG_ADMIN = 1
STAFF = 2
TRAINING_MANAGER = 3
LEARNER = 4

ORG_ROLES = (
    (ORG_ADMIN, 'Admin'),
    (TRAINING_MANAGER, 'Training Manager'),
    (LEARNER, 'LEARNER'),
)
