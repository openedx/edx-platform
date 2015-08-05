"""
Setup script for the Open edX package.
"""

from setuptools import setup

setup(
    name="Open edX",
    version="0.5",
    install_requires=["setuptools"],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorganized to be a more conventional Python tree.
    packages=[
        "openedx.core.djangoapps.course_groups",
        "openedx.core.djangoapps.credit",
        "openedx.core.djangoapps.user_api",
        "lms",
        "cms",
    ],
    entry_points={
        "openedx.course_tab": [
            "ccx = lms.djangoapps.ccx.plugins:CcxCourseTab",
            "courseware = lms.djangoapps.courseware.tabs:CoursewareTab",
            "course_info = lms.djangoapps.courseware.tabs:CourseInfoTab",
            "discussion = lms.djangoapps.django_comment_client.forum.views:DiscussionTab",
            "edxnotes = lms.djangoapps.edxnotes.plugins:EdxNotesTab",
            "external_discussion = lms.djangoapps.courseware.tabs:ExternalDiscussionCourseTab",
            "external_link = lms.djangoapps.courseware.tabs:ExternalLinkCourseTab",
            "html_textbooks = lms.djangoapps.courseware.tabs:HtmlTextbookTabs",
            "instructor = lms.djangoapps.instructor.views.instructor_dashboard:InstructorDashboardTab",
            "notes = lms.djangoapps.notes.views:NotesTab",
            "pdf_textbooks = lms.djangoapps.courseware.tabs:PDFTextbookTabs",
            "progress = lms.djangoapps.courseware.tabs:ProgressTab",
            "static_tab = xmodule.tabs:StaticTab",
            "syllabus = lms.djangoapps.courseware.tabs:SyllabusTab",
            "teams = lms.djangoapps.teams.plugins:TeamsTab",
            "textbooks = lms.djangoapps.courseware.tabs:TextbookTabs",
            "wiki = lms.djangoapps.course_wiki.tab:WikiTab",

            # ORA 1 tabs (deprecated)
            "peer_grading = lms.djangoapps.open_ended_grading.views:PeerGradingTab",
            "staff_grading = lms.djangoapps.open_ended_grading.views:StaffGradingTab",
            "open_ended = lms.djangoapps.open_ended_grading.views:OpenEndedGradingTab",
        ],
        "openedx.user_partition_scheme": [
            "random = openedx.core.djangoapps.user_api.partition_schemes:RandomUserPartitionScheme",
            "cohort = openedx.core.djangoapps.course_groups.partition_scheme:CohortPartitionScheme",
            "verification = openedx.core.djangoapps.credit.partition_schemes:VerificationPartitionScheme",
        ],
    }
)
