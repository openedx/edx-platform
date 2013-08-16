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

    keywords: any xblock field plus (note, the below are filtered out; so, if they
    become legitimate xblock fields, they won't be settable via this factory)
    * org: defaults to textX
    * prettyid: defaults to 999
    * master_branch: (optional) defaults to 'draft'
    * user_id: (optional) defaults to 'test_user'
    * display_name (xblock field): will default to 'Robot Super Course' unless provided
    """
    FACTORY_FOR = CourseDescriptor

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, org='testX', prettyid='999', user_id='test_user', master_branch='draft', **kwargs):

        # Write the data to the mongo datastore
        new_course = modulestore('split').create_course(
            org, prettyid, user_id, fields=kwargs, id_root=prettyid,
            master_branch=master_branch)

        return new_course

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()


class ItemFactory(factory.Factory):
    FACTORY_FOR = XModuleDescriptor

    display_name = factory.LazyAttributeSequence(lambda o, n: "{} {}".format(o.category, n))

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, parent_location, category='chapter',
        user_id='test_user', definition_locator=None, **kwargs):
        """
        passes *kwargs* as the new item's field values:

        :param parent_location: (required) the location of the course & possibly parent

        :param category: (defaults to 'chapter')

        :param definition_locator (optional): the DescriptorLocator for the definition this uses or branches
        """
        return modulestore('split').create_item(
            parent_location, category, user_id, definition_locator, fields=kwargs
        )

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()
