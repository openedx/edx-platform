"""
Modules that get shown to the users when an error has occurred while
loading or rendering other modules
"""


import hashlib
import json
import logging
import sys

import six
from lxml import etree
from xblock.field_data import DictFieldData
from xblock.fields import Scope, ScopeIds, String

from xmodule.errortracker import exc_info_to_str
from xmodule.modulestore import EdxJSONEncoder
from xmodule.x_module import XModule, XModuleDescriptor

log = logging.getLogger(__name__)

# NOTE: This is not the most beautiful design in the world, but there's no good
# way to tell if the module is being used in a staff context or not.  Errors that get discovered
# at course load time are turned into ErrorDescriptor objects, and automatically hidden from students.
# Unfortunately, we can also have errors when loading modules mid-request, and then we need to decide
# what to show, and the logic for that belongs in the LMS (e.g. in get_module), so the error handler
# decides whether to create a staff or not-staff module.


class ErrorFields(object):
    """
    XBlock fields used by the ErrorModules
    """
    contents = String(scope=Scope.content)
    error_msg = String(scope=Scope.content)
    display_name = String(scope=Scope.settings)


class ErrorModule(ErrorFields, XModule):
    """
    Module that gets shown to staff when there has been an error while
    loading or rendering other modules
    """

    def get_html(self):
        '''Show an error to staff.
        TODO (vshnayder): proper style, divs, etc.
        '''
        # staff get to see all the details
        return self.system.render_template('module-error.html', {
            'staff_access': True,
            'data': self.contents,
            'error': self.error_msg,
        })


class NonStaffErrorModule(ErrorFields, XModule):
    """
    Module that gets shown to students when there has been an error while
    loading or rendering other modules
    """
    def get_html(self):
        '''Show an error to a student.
        TODO (vshnayder): proper style, divs, etc.
        '''
        # staff get to see all the details
        return self.system.render_template('module-error.html', {
            'staff_access': False,
            'data': "",
            'error': "",
        })


class ErrorDescriptor(ErrorFields, XModuleDescriptor):
    """
    Module that provides a raw editing view of broken xml.
    """
    module_class = ErrorModule
    resources_dir = None

    def get_html(self):
        return u''

    @classmethod
    def _construct(cls, system, contents, error_msg, location, for_parent=None):
        """
        Build a new ErrorDescriptor. using ``system``.

        Arguments:
            system (:class:`DescriptorSystem`): The :class:`DescriptorSystem` used
                to construct the XBlock that had an error.
            contents (unicode): An encoding of the content of the xblock that had an error.
            error_msg (unicode): A message describing the error.
            location (:class:`UsageKey`): The usage key of the XBlock that had an error.
            for_parent (:class:`XBlock`): Optional. The parent of this error block.
        """

        if error_msg is None:
            # this string is not marked for translation because we don't have
            # access to the user context, and this will only be seen by staff
            error_msg = 'Error not available'

        if location.block_type == 'error':
            location = location.replace(
                # Pick a unique url_name -- the sha1 hash of the contents.
                # NOTE: We could try to pull out the url_name of the errored descriptor,
                # but url_names aren't guaranteed to be unique between descriptor types,
                # and ErrorDescriptor can wrap any type.  When the wrapped module is fixed,
                # it will be written out with the original url_name.
                name=hashlib.sha1(contents.encode('utf8')).hexdigest()
            )

        # real metadata stays in the content, but add a display name
        field_data = DictFieldData({
            'error_msg': six.text_type(error_msg),
            'contents': contents,
            'location': location,
            'category': 'error'
        })
        return system.construct_xblock_from_class(
            cls,
            # The error module doesn't use scoped data, and thus doesn't need
            # real scope keys
            ScopeIds(None, 'error', location, location),
            field_data,
            for_parent=for_parent,
        )

    def get_context(self):
        return {
            'module': self,
            'data': self.contents,
        }

    @classmethod
    def from_json(cls, json_data, system, location, error_msg='Error not available'):
        try:
            json_string = json.dumps(json_data, skipkeys=False, indent=4, cls=EdxJSONEncoder)
        except:  # pylint: disable=bare-except
            json_string = repr(json_data)

        return cls._construct(
            system,
            json_string,
            error_msg,
            location=location
        )

    @classmethod
    def from_descriptor(cls, descriptor, error_msg=None):
        return cls._construct(
            descriptor.runtime,
            str(descriptor),
            error_msg,
            location=descriptor.location,
            for_parent=descriptor.get_parent() if descriptor.has_cached_parent else None
        )

    @classmethod
    def from_xml(cls, xml_data, system, id_generator,  # pylint: disable=arguments-differ
                 error_msg=None):
        '''Create an instance of this descriptor from the supplied data.

        Does not require that xml_data be parseable--just stores it and exports
        as-is if not.

        Takes an extra, optional, parameter--the error that caused an
        issue.  (should be a string, or convert usefully into one).
        '''

        try:
            # If this is already an error tag, don't want to re-wrap it.
            xml_obj = etree.fromstring(xml_data)
            if xml_obj.tag == 'error':
                xml_data = xml_obj.text
                error_node = xml_obj.find('error_msg')
                if error_node is not None:
                    error_msg = error_node.text
                else:
                    error_msg = None

        except etree.XMLSyntaxError:
            # Save the error to display later--overrides other problems
            error_msg = exc_info_to_str(sys.exc_info())

        return cls._construct(system, xml_data, error_msg, location=id_generator.create_definition('error'))

    def export_to_xml(self, resource_fs):
        '''
        If the definition data is invalid xml, export it wrapped in an "error"
        tag.  If it is valid, export without the wrapper.

        NOTE: There may still be problems with the valid xml--it could be
        missing required attributes, could have the wrong tags, refer to missing
        files, etc.  That would just get re-wrapped on import.
        '''
        try:
            xml = etree.fromstring(self.contents)
            return etree.tostring(xml, encoding='unicode')
        except etree.XMLSyntaxError:
            # still not valid.
            root = etree.Element('error')
            root.text = self.contents
            err_node = etree.SubElement(root, 'error_msg')
            err_node.text = self.error_msg
            return etree.tostring(root, encoding='unicode')


class NonStaffErrorDescriptor(ErrorDescriptor):
    """
    Module that provides non-staff error messages.
    """
    module_class = NonStaffErrorModule
