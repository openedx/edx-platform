import jwt


def get_encoded_token(username):
    return jwt.encode({'username': username}, 'secret', algorithm='HS256')
