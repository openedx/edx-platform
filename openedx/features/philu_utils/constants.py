"""
All constants for Philu utils
"""
AWS_S3_PATH = 'https://s3.amazonaws.com/{bucket}/{key}'  # S3 complete path to file

COURSE_CHILD_STRUCTURE = {
    "course": "chapter",
    "chapter": "sequential",
    "sequential": "vertical",
    "vertical": "html",
}
