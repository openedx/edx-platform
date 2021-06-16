""" Rules for permissions of ADG admins """
import rules

from openedx.adg.lms.applications.constants import ADG_ADMIN_GROUP_NAME

# Create rule for ADG specific admin
is_adg_admin = rules.is_group_member(ADG_ADMIN_GROUP_NAME)

# Show Applications section on home screen
rules.add_perm('applications', rules.is_staff)

# User Applications
rules.add_perm('applications.view_userapplication', rules.is_staff)
rules.add_perm('applications.change_userapplication', rules.is_staff)

# Education
rules.add_perm('applications.view_education', rules.is_staff)

# Work Experience
rules.add_perm('applications.view_workexperience', rules.is_staff)

# Business Line
rules.add_perm('applications.view_businessline', rules.is_staff)

# References
rules.add_perm('applications.view_reference', rules.is_staff)
