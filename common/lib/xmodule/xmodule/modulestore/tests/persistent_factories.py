from xmodule.modulestore import ModuleStoreEnum
from xmodule.course_module import CourseDescriptor
from xmodule.x_module import XModuleDescriptor
import factory
from factory.helpers import lazy_attribute


class SplitFactory(factory.Factory):
    """
    Abstracted superclass which defines modulestore so that there's no dependency on django
    if the caller passes modulestore in kwargs
    """
    @lazy_attribute
    def modulestore(self):
        # Delayed import so that we only depend on django if the caller
        # hasn't provided their own modulestore
        from xmodule.modulestore.django import modulestore
        return modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)


class PersistentCourseFactory(SplitFactory):
    """
    Create a new course (not a new version of a course, but a whole new index entry).

    keywords: any xblock field plus (note, the below are filtered out; so, if they
    become legitimate xblock fields, they won't be settable via this factory)
    * org: defaults to textX
    * master_branch: (optional) defaults to ModuleStoreEnum.BranchName.draft
    * user_id: (optional) defaults to 'test_user'
    * display_name (xblock field): will default to 'Robot Super Course' unless provided
    """
    FACTORY_FOR = CourseDescriptor

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, course='999', run='run', org='testX', user_id=ModuleStoreEnum.UserID.test,
                master_branch=ModuleStoreEnum.BranchName.draft, **kwargs):

        modulestore = kwargs.pop('modulestore')
        root_block_id = kwargs.pop('root_block_id', 'course')
        # Write the data to the mongo datastore
        new_course = modulestore.create_course(
            org, course, run, user_id, fields=kwargs,
            master_branch=master_branch, root_block_id=root_block_id
        )

        return new_course

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()


class ItemFactory(SplitFactory):
    FACTORY_FOR = XModuleDescriptor

    display_name = factory.LazyAttributeSequence(lambda o, n: "{} {}".format(o.category, n))

    # pylint: disable=W0613
    @classmethod
    def _create(cls, target_class, parent_location, category='chapter',
                user_id=ModuleStoreEnum.UserID.test, block_id=None, definition_locator=None, force=False,
                continue_version=False, **kwargs):
        """
        passes *kwargs* as the new item's field values:

        :param parent_location: (required) the location of the course & possibly parent

        :param category: (defaults to 'chapter')

        :param definition_locator (optional): the DescriptorLocator for the definition this uses or branches
        """
        modulestore = kwargs.pop('modulestore')
        return modulestore.create_item(
            parent_location, category, user_id, definition_locator=definition_locator,
            block_id=block_id, force=force, continue_version=continue_version, fields=kwargs
        )

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError()
