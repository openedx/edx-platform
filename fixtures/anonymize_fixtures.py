import sys
import json
import random
import copy
from collections import defaultdict
from argparse import ArgumentParser, FileType

def generate_user(user_number):
  return {
    "pk": user_number,
    "model": "auth.user",
    "fields": {
      "status": "w",
      "last_name": "Last",
      "gold": 0,
      "is_staff": False,
      "user_permissions": [],
      "interesting_tags": "",
      "email_key": None,
      "date_joined": "2012-04-26 11:36:39",
      "first_name": "",
      "email_isvalid": False,
      "avatar_type": "n",
      "website": "",
      "is_superuser": False,
      "date_of_birth": None,
      "last_login": "2012-04-26 11:36:48",
      "location": "",
      "new_response_count": 0,
      "email": "user{num}@example.com".format(num=user_number),
      "username": "user{num}".format(num=user_number),
      "is_active": True,
      "consecutive_days_visit_count": 0,
      "email_tag_filter_strategy": 1,
      "groups": [],
      "password": "sha1$90e6f$562a1d783a0c47ce06ebf96b8c58123a0671bbf0",
      "silver": 0,
      "bronze": 0,
      "questions_per_page": 10,
      "about": "",
      "show_country": True,
      "country": "",
      "display_tag_filter_strategy": 0,
      "seen_response_count": 0,
      "real_name": "",
      "ignored_tags": "",
      "reputation": 1,
      "gravatar": "366d981a10116969c568a18ee090f44c",
      "last_seen": "2012-04-26 11:36:39"
    }
  }



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

    for student_id in xrange(args.count):
        out_data.append(generate_user(student_id))

    json.dump(out_data, args.output, indent=2)


if __name__ == "__main__":
    sys.exit(main())
