from faker import Faker
from opaque_keys.edx.keys import CourseKey

fake = Faker()


def random_course_key():
    """
    Generate a CourseKey object from a random string {3 characters}/{4 digits}/course
    """
    return CourseKey.from_string('{random_str}/{random_int}/course'.format(
        random_str=fake.pystr(max_chars=3),
        random_int=fake.random_number(digits=4)
    ))
