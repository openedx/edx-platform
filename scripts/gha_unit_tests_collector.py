import sys
import os
import yaml
import argparse


def get_all_unit_test_modules():
    unit_tests_yml = f'{os.getcwd()}/.github/workflows/unit-tests.yml'
    with open(unit_tests_yml) as file:
        unit_test_workflow_yaml = yaml.safe_load(file)

    return unit_test_workflow_yaml['jobs']['run-tests']['strategy']['matrix']['test_module']


def get_modules_except_cms():
    all_unit_test_modules = get_all_unit_test_modules()
    return [module for module in all_unit_test_modules if not module.startswith('cms')]


def get_cms_modules():
    all_unit_test_modules = get_all_unit_test_modules()
    return [module for module in all_unit_test_modules if module.startswith('cms')]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cms-only", action="store_true", default="")
    parser.add_argument("--lms-only", action="store_true", default="")

    argument = parser.parse_args()

    if argument.lms_only:
        modules = get_modules_except_cms()
    elif argument.cms_only:
        modules = get_cms_modules()
    else:
        modules = get_all_unit_test_modules()

    unit_test_paths = ' '.join(modules)
    sys.stdout.write(unit_test_paths)
