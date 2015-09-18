#TODO: move this file to a more appropriate location, in a real folder

def parse_some_stuff():
    """
    parse any and all environment variables here
    """

def set_up_team_config():
    """
    initial contact with studio to set up team config
    model this after the code in https://github.com/edx/load-tests/blob/master/locust/team_init/locustfile.py
    """

def read_enrollment_data():
    """
    read user_id or usernames from provided csv file
    """

def enroll_in_random_team(student):
    """
    do what the name of this method says
    """

if __name__ == "__main__":
    parse_some_stuff()
    set_up_team_config()
    read_enrollment_data()
    for student in enrollment_data:
        enroll_in_random_team(student)
