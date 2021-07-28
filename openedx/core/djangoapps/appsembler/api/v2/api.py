from student.models import (email_exists_or_retired,
                            username_exists_or_retired)


def email_exists(email):
    return email and email_exists_or_retired(email, check_for_new_site=False)


def username_exists(username):
    return username and username_exists_or_retired(username)
