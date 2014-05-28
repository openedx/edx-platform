"""
Module contains utils specific for video_module but not for transcripts.
"""


def create_youtube_string(module):
    """
    Create a string of Youtube IDs from `module`'s metadata
    attributes. Only writes a speed if an ID is present in the
    module.  Necessary for backwards compatibility with XML-based
    courses.
    """
    youtube_ids = [
        module.youtube_id_0_75,
        module.youtube_id_1_0,
        module.youtube_id_1_25,
        module.youtube_id_1_5
    ]
    youtube_speeds = ['0.75', '1.00', '1.25', '1.50']
    return ','.join([
        ':'.join(pair)
        for pair
        in zip(youtube_speeds, youtube_ids)
        if pair[1]
    ])


def get_course_for_item(module):
    '''
    Get course for item.

    This is workaround and can be removed as soos as
    ihneritance will work for video descriptor.
    '''
    return module.runtime.modulestore.get_course(module.location.course_key, depth=0)
