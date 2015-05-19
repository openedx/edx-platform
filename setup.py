"""
Setup script for the Open edX package.
"""

from setuptools import setup

setup(
    name="Open edX",
    version="0.3",
    install_requires=["distribute"],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorganized to be a more conventional Python tree.
    packages=[
        "openedx.core.djangoapps.course_groups",
        "openedx.core.djangoapps.user_api",
        "lms",
        "cms",
    ],
    entry_points={
        "openedx.course_view_type": [
            "ccx = lms.djangoapps.ccx.plugins:CcxCourseViewType",
            "courseware = lms.djangoapps.courseware.tabs:CoursewareViewType",
            "course_info = lms.djangoapps.courseware.tabs:CourseInfoViewType",
            "discussion = lms.djangoapps.django_comment_client.forum.views:DiscussionCourseViewType",
            "edxnotes = lms.djangoapps.edxnotes.plugins:EdxNotesCourseViewType",
            "external_discussion = lms.djangoapps.courseware.tabs:ExternalDiscussionCourseViewType",
            "external_link = lms.djangoapps.courseware.tabs:ExternalLinkCourseViewType",
            "html_textbooks = lms.djangoapps.courseware.tabs:HtmlTextbookCourseViews",
            "instructor = lms.djangoapps.instructor.views.instructor_dashboard:InstructorDashboardViewType",
            "notes = lms.djangoapps.notes.views:NotesCourseViewType",
            "pdf_textbooks = lms.djangoapps.courseware.tabs:PDFTextbookCourseViews",
            "progress = lms.djangoapps.courseware.tabs:ProgressCourseViewType",
            "static_tab = lms.djangoapps.courseware.tabs:StaticCourseViewType",
            "syllabus = lms.djangoapps.courseware.tabs:SyllabusCourseViewType",
            "textbooks = lms.djangoapps.courseware.tabs:TextbookCourseViews",
            "wiki = lms.djangoapps.course_wiki.tab:WikiCourseViewType",

            # ORA 1 tabs (deprecated)
            "peer_grading = lms.djangoapps.open_ended_grading.views:PeerGradingTab",
            "staff_grading = lms.djangoapps.open_ended_grading.views:StaffGradingTab",
            "open_ended = lms.djangoapps.open_ended_grading.views:OpenEndedGradingTab",
        ],
        "openedx.user_partition_scheme": [
            "random = openedx.core.djangoapps.user_api.partition_schemes:RandomUserPartitionScheme",
            "cohort = openedx.core.djangoapps.course_groups.partition_scheme:CohortPartitionScheme",
        ],
    }
)
