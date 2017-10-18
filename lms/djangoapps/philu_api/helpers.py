import jwt


def get_encoded_token(username):
    print(id, username)
    return jwt.encode({'username': username}, 'secret', algorithm='HS256')
