import os
import copy
import re
import sys
from pathlib import Path

FIRST_PATTERN = r"^(.*@extend) %(.*);\n?"
SECOND_PATTERN = r"^(.*@extend) \.(.*);\n?"

FIRST_SUBSTITUTE = r"\1 %\2 !optional;\n"
SECOND_SUBSTITUTE = r"\1 .\2 !optional;\n"

PATTERNS = {FIRST_PATTERN: FIRST_SUBSTITUTE, SECOND_PATTERN: SECOND_SUBSTITUTE}


def get_match(string):
    for pattern, substitute in PATTERNS.items():
        match = re.match(pattern, string)
        if match is None:
            continue
        return match, pattern, substitute
    return None, None, None


def process_file(file_path):
    with open(file_path, 'r') as file:
        file_content = file.readlines()
        print("processing {0}".format(file_path))
        data_clone = copy.deepcopy(file_content)
        for index, line in enumerate(file_content):
            match, pattern, substitute = get_match(line)
            if match is None or "!optional" in line:
                continue
            updated_line = re.sub(pattern, substitute, line)
            data_clone[index] = updated_line
    return data_clone


def update_file(path, updated_data):
    with open(path, 'w') as file:
        file.writelines(updated_data)


def process_files(directory):
    for path in Path(directory).rglob('*.scss'):
        updated_data = process_file(str(path))
        update_file(str(path), updated_data)


if __name__ == '__main__':
    file_to_process = sys.argv[1]
    updated_data_a = process_file(file_to_process)
    update_file(file_to_process, updated_data_a)

    # print("processing LMS...")
    # process_files("lms")
    #
    # print("processing themes...")
    # process_files("themes")
    #
    # print("processing CMS...")
    # process_files("cms")
    #
    # print("processing common...")
    # process_files("common")
