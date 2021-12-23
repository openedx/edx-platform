import sys
import os
import argparse
import json


def get_test_paths_for_shard(shard_name, output):
    unit_tests_json = f'{os.getcwd()}/.github/workflows/unit-test-shards.json'
    with open(unit_tests_json) as file:
        unit_test_workflow_shards = json.loads(file.read())

    if shard_name not in unit_test_workflow_shards:
        sys.stdout.write("Error, invalid shard name provided. please provide a valid shard name as specified in unit-test-shards.json")

    return unit_test_workflow_shards.get(shard_name).get(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-name", action="store", default="")
    parser.add_argument("--output", action="store", default="path", choices=["path", "settings"])
    argument = parser.parse_args()

    if not argument.shard_name:
        sys.exit("Error, no shard name provided. please provide a valid shard name as specified in unit-test-shards.json")

    unit_test_paths = get_test_paths_for_shard(argument.shard_name, argument.output)
    sys.stdout.write(unit_test_paths)
