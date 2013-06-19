from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from xmodule.x_module import XModuleDescriptor
import factory


# [dhm] I'm not sure why we're using factory_boy if we're not following its pattern. If anyone
# assumes they can call build, it will completely fail, for example.
# pylint: disable=W0232
class PersistentCourseFactory(factory.Factory):
    """
    Create a new course (not a new version of a course, but a whole new index entry).

    keywords:
    * org: defaults to textX
    * prettyid: defaults to 999
    * display_name
    * user_id
    * data (optional) the data payload to save in the course item
    * metadata (optional) the metadata payload. If display_name is in the metadata, that takes
    precedence over any display_name provided directly.
    """
    FACTORY_FOR = CourseDescriptor

    org = 'testX'
    prettyid = '999'
    display_name = 'Robot Super Course'
    user_id = "test_user"
    data = None
    metadata = None
    master_version = 'draft'

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, *args, **kwargs):

        org = kwargs.get('org')
        prettyid = kwargs.get('prettyid')
        display_name = kwargs.get('display_name')
        user_id = kwargs.get('user_id')
        data = kwargs.get('data')
        metadata = kwargs.get('metadata', {})
        if metadata is None:
            metadata = {}
        if 'display_name' not in metadata:
            metadata['display_name'] = display_name

        # Write the data to the mongo datastore
        new_course = modulestore('split').create_course(
            org, prettyid, user_id, metadata=metadata, course_data=data, id_root=prettyid,
            master_version=kwargs.get('master_version'))

        return new_course

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()


class ItemFactory(factory.Factory):
    FACTORY_FOR = XModuleDescriptor

    category = 'chapter'
    user_id = 'test_user'
    display_name = factory.LazyAttributeSequence(lambda o, n: "{} {}".format(o.category, n))

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        """
        Uses *kwargs*:

        *parent_location* (required): the location of the course & possibly parent

        *category* (defaults to 'chapter')

        *data* (optional): the data for the item

        definition_locator (optional): the DescriptorLocator for the definition this uses or branches

        *display_name* (optional): the display name of the item

        *metadata* (optional): dictionary of metadata attributes (display_name here takes
        precedence over the above attr)
        """
        metadata = kwargs.get('metadata', {})
        if 'display_name' not in metadata and 'display_name' in kwargs:
            metadata['display_name'] = kwargs['display_name']

        return modulestore('split').create_item(kwargs['parent_location'], kwargs['category'],
            kwargs['user_id'], definition_locator=kwargs.get('definition_locator'),
            new_def_data=kwargs.get('data'), metadata=metadata)

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()
