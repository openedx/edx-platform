"""
Simple utility functions that operate on block metadata.

This is a place to put simple functions that operate on block metadata. It
allows us to share code between the XModuleMixin and CourseOverview and
BlockStructure.
"""


def url_name_for_block(block):
    """
    Given a block, returns the block's URL name.

    Arguments:
        block (XModuleMixin|CourseOverview|BlockStructureBlockData):
            Block that is being accessed
    """
    return block.location.name


def display_name_with_default(block):
    """
    Calculates the display name for a block.

    Default to the display_name if it isn't None, else fall back to creating
    a name based on the URL.

    Unlike the rest of this module's functions, this function takes an entire
    course descriptor/overview as a parameter. This is because a few test cases
    (specifically, {Text|Image|Video}AnnotationModuleTestCase.test_student_view)
    create scenarios where course.display_name is not None but course.location
    is None, which causes calling course.url_name to fail. So, although we'd
    like to just pass course.display_name and course.url_name as arguments to
    this function, we can't do so without breaking those tests.

    Note: This method no longer escapes as it once did, so the caller must
    ensure it is properly escaped where necessary.

    Arguments:
        block (XModuleMixin|CourseOverview|BlockStructureBlockData):
            Block that is being accessed
    """
    return (
        block.display_name if block.display_name is not None
        else url_name_for_block(block).replace('_', ' ')
    )


def display_name_with_default_escaped(block):
    """
    DEPRECATED: use display_name_with_default

    Calculates the display name for a block with some HTML escaping.
    This follows the same logic as display_name_with_default, with
    the addition of the escaping.

    Here is an example of how to move away from this method in Mako html:
        Before:
        <span class="course-name">${course.display_name_with_default_escaped}</span>

        After:
        <span class="course-name">${course.display_name_with_default | h}</span>
    If the context is Javascript in Mako, you'll need to follow other best practices.

    Note: Switch to display_name_with_default, and ensure the caller
    properly escapes where necessary.

    Note: This newly introduced method should not be used.  It was only
    introduced to enable a quick search/replace and the ability to slowly
    migrate and test switching to display_name_with_default, which is no
    longer escaped.

    Arguments:
        block (XModuleMixin|CourseOverview|BlockStructureBlockData):
            Block that is being accessed
    """
    # This escaping is incomplete.  However, rather than switching this to use
    # markupsafe.escape() and fixing issues, better to put that energy toward
    # migrating away from this method altogether.
    return display_name_with_default(block).replace('<', '&lt;').replace('>', '&gt;')
