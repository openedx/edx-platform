import jwt


def get_encoded_token(username, email, id):
    return jwt.encode({'id': id, 'username': username, 'email': email }, 'secret', algorithm='HS256')
