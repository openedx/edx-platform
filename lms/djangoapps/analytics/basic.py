"""
Student and course analytics.

Serve miscellaneous course and student data
"""

from django.contrib.auth.models import User
import xmodule.graders as xmgraders


AVAILABLE_STUDENT_FEATURES = ['username', 'first_name', 'last_name', 'is_staff', 'email']
AVAILABLE_PROFILE_FEATURES = ['name', 'language', 'location', 'year_of_birth', 'gender', 'level_of_education', 'mailing_address', 'goals']


def enrolled_students_profiles(course_id, features):
    """
    Return array of student features e.g. [{?}, ...]
    """
    # enrollments = CourseEnrollment.objects.filter(course_id=course_id)
    # students = [enrollment.user for enrollment in enrollments]
    students = User.objects.filter(courseenrollment__course_id=course_id).order_by('username').select_related('profile')

    def extract_student(student):
        student_features = [feature for feature in features if feature in AVAILABLE_STUDENT_FEATURES]
        profile_features = [feature for feature in features if feature in AVAILABLE_PROFILE_FEATURES]

        student_dict = dict((feature, getattr(student, feature)) for feature in student_features)
        profile = student.profile
        profile_dict = dict((feature, getattr(profile, feature)) for feature in profile_features)
        student_dict.update(profile_dict)
        return student_dict

    return [extract_student(student) for student in students]


def dump_grading_context(course):
    """
    Dump information about course grading context (eg which problems are graded in what assignments)
    Useful for debugging grading_policy.json and policy.json

    Returns HTML string
    """
    msg = "-----------------------------------------------------------------------------\n"
    msg += "Course grader:\n"

    msg += '%s\n' % course.grader.__class__
    graders = {}
    if isinstance(course.grader, xmgraders.WeightedSubsectionsGrader):
        msg += '\n'
        msg += "Graded sections:\n"
        for subgrader, category, weight in course.grader.sections:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n" % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += "-----------------------------------------------------------------------------\n"
    msg += "Listing grading context for course %s\n" % course.id

    gc = course.grading_context
    msg += "graded sections:\n"

    msg += '%s\n' % gc['graded_sections'].keys()
    for (gs, gsvals) in gc['graded_sections'].items():
        msg += "--> Section %s:\n" % (gs)
        for sec in gsvals:
            s = sec['section_descriptor']
            format = getattr(s.lms, 'format', None)
            aname = ''
            if format in graders:
                g = graders[format]
                aname = '%s %02d' % (g.short_label, g.index)
                g.index += 1
            elif s.display_name in graders:
                g = graders[s.display_name]
                aname = '%s' % g.short_label
            notes = ''
            if getattr(s, 'score_by_attempt', False):
                notes = ', score by attempt!'
            msg += "      %s (format=%s, Assignment=%s%s)\n" % (s.display_name, format, aname, notes)
    msg += "all descriptors:\n"
    msg += "length=%d\n" % len(gc['all_descriptors'])
    msg = '<pre>%s</pre>' % msg.replace('<','&lt;')
    return msg
