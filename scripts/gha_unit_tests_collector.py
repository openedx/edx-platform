import sys
import os
import yaml
import argparse
import json


def get_all_unit_test_shards():
    unit_tests_json = f'{os.getcwd()}/.github/workflows/unit-test-shards.json'
    with open(unit_tests_json) as file:
        unit_test_workflow_shards = json.loads(file.read())

    return unit_test_workflow_shards


def get_modules_except_cms():
    all_unit_test_shards = get_all_unit_test_shards()
    return [paths for shard_name, paths in all_unit_test_shards.items() if not paths.startswith('cms')]


def get_cms_modules():
    all_unit_test_shards = get_all_unit_test_shards()
    return [paths for shard_name, paths in all_unit_test_shards.items() if paths.startswith('cms')]


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
