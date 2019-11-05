"""
Module to put all pytest hooks for various
"""

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
