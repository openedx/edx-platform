from xmodule import course_module

from . import mixins

import logging
logger = logging.getLogger(__name__)


def get_CourseDescriptor_mixins():

    new_mixins = []
    new_mixins.append(mixins.MsftLPMixin)

    return tuple(new_mixins)

logger.warn('Monkeypatching course_module.CourseDescriptor to add Appsembler Mixins')
orig_CourseDescriptor = course_module.CourseDescriptor
CDbases = course_module.CourseDescriptor.__bases__
course_module.CourseDescriptor.__bases__ = get_CourseDescriptor_mixins() + CDbases
