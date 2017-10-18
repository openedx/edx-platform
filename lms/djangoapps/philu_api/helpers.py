import jwt


def get_encoded_token(username, email):
    return jwt.encode({'username': username, 'email': email}, 'secret', algorithm='HS256')
