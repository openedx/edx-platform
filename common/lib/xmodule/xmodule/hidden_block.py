"""
HiddenBlock is a placeholder for when we don't have a registered block type
for some given tag.
"""
from xblock.core import XBlock
from xblock.fragment import Fragment


@XBlock.needs('user')
class HiddenBlock(XBlock):
    """
    HiddenBlock is the XBlock invoked when we can't find the actual block type
    we want. This most commonly happens if the appropriate XBlock isn't
    installed properly.
    """

    HIDDEN = True

    def student_view(self, _context):
        """Returns a simple error message if the user is staff."""
        fragment = Fragment()

        if self._is_staff():
            msg = u"ERROR: This module is unknown--students will not see it at all"
        else:
            msg = ""
        fragment.add_content(msg)

        return fragment

    def author_view(self, _context):
        """View for Studio display -- identical to the student_view."""
        return self.student_view(_context)

    def _is_staff(self):
        """Helper to determine whether a user is staff in an XBlock compatible way."""
        user_service = self.runtime.service(self, 'user')
        xb_user = user_service.get_current_user()

        # Seriously, why isn't this just a part of the user service?
        return xb_user.opt_attrs.get('edx-platform.user_is_staff', False)
