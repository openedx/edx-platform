"""
Student and course analytics.

Serve miscellaneous course and student data
"""

import xmodule.graders as xmgraders

def _dump_grading_context(course):
    """
    Dump information about course grading context (eg which problems are graded in what assignments)
    Very useful for debugging grading_policy.json and policy.json

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
