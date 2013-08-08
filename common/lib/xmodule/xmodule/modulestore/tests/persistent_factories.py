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
    * fields (optional) the settings and content payloads. If display_name is in the metadata, that takes
    precedence over any display_name provided directly.
    """
    FACTORY_FOR = CourseDescriptor

    org = 'testX'
    prettyid = '999'
    display_name = 'Robot Super Course'
    user_id = "test_user"
    data = None
    metadata = None
    master_branch = 'draft'

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, *args, **kwargs):

        org = kwargs.get('org')
        prettyid = kwargs.get('prettyid')
        display_name = kwargs.get('display_name')
        user_id = kwargs.get('user_id')
        fields = kwargs.get('fields', {})
        if display_name and 'display_name' not in fields:
            fields['display_name'] = display_name

        # Write the data to the mongo datastore
        new_course = modulestore('split').create_course(
            org, prettyid, user_id, fields=fields, id_root=prettyid,
            master_branch=kwargs.get('master_branch'))

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

        :param parent_location: (required) the location of the course & possibly parent

        :param category: (defaults to 'chapter')

        :param fields: (optional) the data for the item

        :param definition_locator (optional): the DescriptorLocator for the definition this uses or branches

        :param display_name (optional): the display name of the item
        """
        fields = kwargs.get('fields', {})
        if 'display_name' not in fields and 'display_name' in kwargs:
            fields['display_name'] = kwargs['display_name']

        return modulestore('split').create_item(kwargs['parent_location'], kwargs['category'],
            kwargs['user_id'], definition_locator=kwargs.get('definition_locator'),
            fields=fields)

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()
