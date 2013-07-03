"""
Student and course analytics.

Serve miscellaneous course and student data
"""

from django.contrib.auth.models import User
import xmodule.graders as xmgraders


STUDENT_FEATURES = ('username', 'first_name', 'last_name', 'is_staff', 'email')
PROFILE_FEATURES = ('name', 'language', 'location', 'year_of_birth', 'gender',
                    'level_of_education', 'mailing_address', 'goals')
AVAILABLE_FEATURES = STUDENT_FEATURES + PROFILE_FEATURES


def enrolled_students_profiles(course_id, features):
    """
    Return list of student features as dictionaries.

    enrolled_students_profiles(course_id, ['username, first_name'])
    would return [
        {'username': 'username1', 'first_name': 'firstname1'}
        {'username': 'username2', 'first_name': 'firstname2'}
        {'username': 'username3', 'first_name': 'firstname3'}
    ]
    """
    students = User.objects.filter(courseenrollment__course_id=course_id)\
        .order_by('username').select_related('profile')

    def extract_student(student, features):
        """ convert student to dictionary """
        student_features = [x for x in STUDENT_FEATURES if x in features]
        profile_features = [x for x in PROFILE_FEATURES if x in features]

        student_dict = dict((feature, getattr(student, feature))
                            for feature in student_features)
        profile = student.profile
        profile_dict = dict((feature, getattr(profile, feature))
                            for feature in profile_features)
        student_dict.update(profile_dict)
        return student_dict

    return [extract_student(student, features) for student in students]


def dump_grading_context(course):
    """
    Render information about course grading context
    (e.g. which problems are graded in what assignments)
    Useful for debugging grading_policy.json and policy.json

    Returns HTML string
    """
    hbar = "{}\n".format("-" * 77)
    msg = hbar
    msg += "Course grader:\n"

    msg += '%s\n' % course.grader.__class__
    graders = {}
    if isinstance(course.grader, xmgraders.WeightedSubsectionsGrader):
        msg += '\n'
        msg += "Graded sections:\n"
        for subgrader, category, weight in course.grader.sections:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n"\
                % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += hbar
    msg += "Listing grading context for course %s\n" % course.id

    gcontext = course.grading_context
    msg += "graded sections:\n"

    msg += '%s\n' % gcontext['graded_sections'].keys()
    for (gsomething, gsvals) in gcontext['graded_sections'].items():
        msg += "--> Section %s:\n" % (gsomething)
        for sec in gsvals:
            sdesc = sec['section_descriptor']
            frmat = getattr(sdesc.lms, 'format', None)
            aname = ''
            if frmat in graders:
                gform = graders[frmat]
                aname = '%s %02d' % (gform.short_label, gform.index)
                gform.index += 1
            elif sdesc.display_name in graders:
                gform = graders[sdesc.display_name]
                aname = '%s' % gform.short_label
            notes = ''
            if getattr(sdesc, 'score_by_attempt', False):
                notes = ', score by attempt!'
            msg += "      %s (format=%s, Assignment=%s%s)\n"\
                % (sdesc.display_name, frmat, aname, notes)
    msg += "all descriptors:\n"
    msg += "length=%d\n" % len(gcontext['all_descriptors'])
    msg = '<pre>%s</pre>' % msg.replace('<', '&lt;')
    return msg
