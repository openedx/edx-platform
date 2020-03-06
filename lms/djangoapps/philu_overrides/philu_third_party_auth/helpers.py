from django.core.exceptions import ValidationError

from student.forms import validate_username


def normalize_pipeline_kwargs(pipeline_kwargs):
    username = pipeline_kwargs.get('username')
    if username:
        try:
            validate_username(username)
        except ValidationError:
            pipeline_kwargs['username'] = ''
    return pipeline_kwargs
