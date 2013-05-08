OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'blah/',
    'username': 'incorrect',
    'password': 'incorrect',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller'
}

S3_INTERFACE = {
    'aws_access_key': "",
    'aws_secret_key': "",
    "aws_bucket_name": "",
}

class MockQueryDict(dict):
    """
    Mock a query set so that it can be used with default authorization
    """
    def getlist(self, key, default=None):
        try:
            return super(MockQueryDict, self).__getitem__(key)
        except KeyError:
            if default is None:
                return []
        return default