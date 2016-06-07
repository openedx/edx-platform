"""
======== Offline calculation of grades =============================================================

Computing grades of a large number of students can take a long time.  These routines allow grades to
be computed offline, by a batch process (eg cronjob).

The grades are stored in the OfflineComputedGrade table of the courseware model.
"""
import json
import time

from json import JSONEncoder
from courseware import grades, models
from courseware.courses import get_course_by_id
from django.contrib.auth.models import User
from opaque_keys import OpaqueKey
from opaque_keys.edx.keys import UsageKey
from xmodule.graders import Score

from instructor.utils import DummyRequest


class MyEncoder(JSONEncoder):
    """ JSON Encoder that can encode OpaqueKeys """
    def default(self, obj):  # pylint: disable=method-hidden
        """ Encode an object that the default encoder hasn't been able to. """
        if isinstance(obj, OpaqueKey):
            return unicode(obj)
        return JSONEncoder.default(self, obj)


def offline_grade_calculation(course_key):
    '''
    Compute grades for all students for a specified course, and save results to the DB.
    '''

    tstart = time.time()
    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1
    ).prefetch_related("groups").order_by('username')

    enc = MyEncoder()

    print "{} enrolled students".format(len(enrolled_students))
    course = get_course_by_id(course_key)

    for student in enrolled_students:
        request = DummyRequest()
        request.user = student
        request.session = {}

        gradeset = grades.grade(student, request, course, keep_raw_scores=True)
        # Convert Score namedtuples to dicts:
        totaled_scores = gradeset['totaled_scores']
        for section in totaled_scores:
            totaled_scores[section] = [score._asdict() for score in totaled_scores[section]]
        gradeset['raw_scores'] = [score._asdict() for score in gradeset['raw_scores']]
        # Encode as JSON and save:
        gradeset_str = enc.encode(gradeset)
        ocg, _created = models.OfflineComputedGrade.objects.get_or_create(user=student, course_id=course_key)
        ocg.gradeset = gradeset_str
        ocg.save()
        print "%s done" % student  	# print statement used because this is run by a management command

    tend = time.time()
    dt = tend - tstart

    ocgl = models.OfflineComputedGradeLog(course_id=course_key, seconds=dt, nstudents=len(enrolled_students))
    ocgl.save()
    print ocgl
    print "All Done!"


def offline_grades_available(course_key):
    '''
    Returns False if no offline grades available for specified course.
    Otherwise returns latest log field entry about the available pre-computed grades.
    '''
    ocgl = models.OfflineComputedGradeLog.objects.filter(course_id=course_key)
    if not ocgl:
        return False
    return ocgl.latest('created')


def student_grades(student, request, course, keep_raw_scores=False, use_offline=False):
    '''
    This is the main interface to get grades.  It has the same parameters as grades.grade, as well
    as use_offline.  If use_offline is True then this will look for an offline computed gradeset in the DB.
    '''
    if not use_offline:
        return grades.grade(student, request, course, keep_raw_scores=keep_raw_scores)

    try:
        ocg = models.OfflineComputedGrade.objects.get(user=student, course_id=course.id)
    except models.OfflineComputedGrade.DoesNotExist:
        return dict(
            raw_scores=[],
            section_breakdown=[],
            msg='Error: no offline gradeset available for {}, {}'.format(student, course.id)
        )

    gradeset = json.loads(ocg.gradeset)
    # Convert score dicts back to Score tuples:

    def score_from_dict(encoded):
        """ Given a formerly JSON-encoded Score tuple, return the Score tuple """
        if encoded['module_id']:
            encoded['module_id'] = UsageKey.from_string(encoded['module_id'])
        return Score(**encoded)

    totaled_scores = gradeset['totaled_scores']
    for section in totaled_scores:
        totaled_scores[section] = [score_from_dict(score) for score in totaled_scores[section]]
    gradeset['raw_scores'] = [score_from_dict(score) for score in gradeset['raw_scores']]
    return gradeset
