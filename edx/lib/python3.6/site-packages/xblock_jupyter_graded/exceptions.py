
class ValidationError(Exception):
    """Validation based errors"""
    def __init__(self, msg, status_code=None):
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return self.msg


class DockerBuildError(Exception):
    """Errors emmitted when building Docker Containers"""
    pass


class DockerContainerError(Exception):
    """Errors emmitted when running Docker Containers"""
    pass
