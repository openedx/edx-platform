"""
Module to put all pytest hooks for various
"""
import os
import json

def pytest_json_modifyreport(json_report):
    """
    The function is called by pytest-json-report plugin to only output warnings in json format.
    Everything else is removed due to it already being saved by junitxml
    The json warning outputs are meant to be read by jenkins
    """
    warnings_flag = 'warnings'
    if warnings_flag in json_report:
        warnings = json_report[warnings_flag]
        json_report.clear()
        json_report[warnings_flag] = warnings
    else:
        json_report = {}
    return json_report


def create_file_name(file_name, num=0):
    name = file_name 
    if num != 0:
        name = name + str(num)
    return name + ".json"


def pytest_sessionfinish(session):
    """
    Since multiple pytests are running, 
    this makes sure warnings from different run are not overwritten 
    """
    file_name_prefix = "test_root/log/warnings"
    num = 0
    # to make sure this doesn't loop forever, putting a maximum
    while os.path.isfile(create_file_name(file_name_prefix, num)) and num < 10:
        num += 1

    report = session.config._json_report.report

    with open(create_file_name(file_name_prefix, num), 'w') as outfile:
        json.dump(report, outfile)