"""
'library' XBlock/XModule

The "library" XBlock/XModule is the root of every content library structure
tree. All content blocks in the library are its children. It is analagous to
the "course" XBlock/XModule used as the root of each normal course structure
tree.
"""
import logging

from xmodule.vertical_module import VerticalDescriptor, VerticalModule

from xblock.fields import Scope, String, List

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class LibraryFields(object):
    """
    Fields of the "library" XBlock - see below.
    """
    display_name = String(
        help=_("Enter the name of the library as it should appear in Studio."),
        default="Library",
        display_name=_("Library Display Name"),
        scope=Scope.settings
    )
    advanced_modules = List(
        display_name=_("Advanced Module List"),
        help=_("Enter the names of the advanced components to use in your library."),
        scope=Scope.settings
    )
    has_children = True


class LibraryDescriptor(LibraryFields, VerticalDescriptor):
    """
    Descriptor for our library XBlock/XModule.
    """
    module_class = VerticalModule

    def __init__(self, *args, **kwargs):
        """
        Expects the same arguments as XModuleDescriptor.__init__
        """
        super(LibraryDescriptor, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u"Library: {}".format(self.display_name)

    def __str__(self):
        return "Library: {}".format(self.display_name)

    @property
    def display_org_with_default(self):
        """
        Org display names are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'org' field from the key.
        """
        return self.location.course_key.org

    @property
    def display_number_with_default(self):
        """
        Display numbers are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'library' field from the key.
        """
        return self.location.course_key.library

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """ XML support not yet implemented. """
        raise NotImplementedError

    def export_to_xml(self, resource_fs):
        """ XML support not yet implemented. """
        raise NotImplementedError
