import sys
import json
import random
import copy
from collections import defaultdict
from argparse import ArgumentParser, FileType


def parse_args(args=sys.argv[1:]):
    parser = ArgumentParser()
    parser.add_argument('-d', '--data', type=FileType('r'), default=sys.stdin)
    parser.add_argument('-o', '--output', type=FileType('w'), default=sys.stdout)
    parser.add_argument('count', type=int)
    return parser.parse_args(args)

def main(args=sys.argv[1:]):
    args = parse_args(args)

    data = json.load(args.data)
    unique_students = set(entry['fields']['student'] for entry in data)
    if args.count > len(unique_students) * 0.1:
        raise Exception("Can't be sufficiently anonymous selecting {count} of {unique} students".format(
            count=args.count, unique=len(unique_students)))

    by_problems = defaultdict(list)
    for entry in data:
        by_problems[entry['fields']['module_id']].append(entry)

    out_data = []
    out_pk = 1
    for name, answers in by_problems.items():
        for student_id in xrange(args.count):
            sample = random.choice(answers)
            data = copy.deepcopy(sample)
            data["fields"]["student"] = student_id + 1
            data["pk"] = out_pk
            out_pk += 1
            out_data.append(data)

    json.dump(out_data, args.output, indent=2)

if __name__ == "__main__":
    sys.exit(main())
