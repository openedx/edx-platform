from setuptools import setup, find_packages

setup(
    name="XModule",
    version="0.1",
    packages=find_packages(),
    install_requires=['distribute'],
    entry_points={
        'xmodule.v1': [
            "Course = seq_module:SectionDescriptor",
            "Week = seq_module:WeekDescriptor",
            "Section = seq_module:SectionDescriptor",
            "LectureSequence = seq_module:SectionDescriptor",
            "Lab = seq_module:SectionDescriptor",
            "Homework = seq_module:SectionDescriptor",
            "TutorialIndex = seq_module:SectionDescriptor",
            "Exam = seq_module:SectionDescriptor",
            "VideoSegment = video_module:VideoSegmentDescriptor",
        ]
    }
)
