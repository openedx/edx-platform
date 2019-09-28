#!/usr/bin/env python3

import argparse
import hashlib
import random
import re
import string

if "choices" not in dir(random):
    raise ImportError("Python 3.6+ required for random.choices")
#####


###  Main  ###
def main(args, env):
    epilog = "Checks username bucketing for experiments and generates names for each experiment bucket.  Derived names include the base user name, experiment abbreviation, bucket number, and a short random string, separated with hyphens.  (v1.0)"
    parser = argparse.ArgumentParser(epilog=epilog)
    parser.add_argument(
        "exp",
        metavar="EXPERIMENT",
        help="Experiment to bucket for.",
    )
    parser.add_argument(
        "user",
        nargs="?",
        default=env.get("USER", ""),
        metavar="NAME",
        help="Base user name for bucketing, default is $USER.",
    )
    parser.add_argument(
        "-a", "--abbrev",
        metavar="EXP",
        help="Experiment abbreviation for name generation.",
    )
    parser.add_argument(
        "-b", "--buckets",
        nargs="+",
        type=int,
        metavar="X",
        help="Buckets to make names for, default is all buckets.",
    )
    parser.add_argument(
        "-c", "--check-only",
        action="store_true",
        help="Just check what bucket the user is in, don't generate names.",
    )
    parser.add_argument(
        "-n", "--number",
        type=int,
        default=2,
        metavar="N",
        help="Number of buckets, default is 2.",
    )
    parser.add_argument(
        "--print-args",
        action="store_true",
        # help="Print arguments and computations, then exit.",
        help=argparse.SUPPRESS,
    )
    my_args = parser.parse_args(sys.argv[1:])

    hash = hash_exp(my_args.exp, my_args.user)
    digest = bucket_int(hash)
    bucket = digest % my_args.number

    print(f"{my_args.user} is in bucket: {bucket}")
    if my_args.print_args:
        print(f"* Args:\n\t{my_args}\n* Computed:\n\tdigest: {digest} - hash: {hash} - {abbreviate(my_args.exp)}")
        return 0

    if my_args.check_only:
        return 0

    abbrev = my_args.abbrev
    if abbrev is None:
        abbrev = abbreviate(my_args.exp)

    bucket_list = my_args.buckets
    if not bucket_list:
        bucket_list = range(my_args.number)

    # TODO: validate more of the arguments
    # HACK: currently not enforcing the naming rules:
    # - Username must be between 2 and 30 characters long. 
    # - Usernames can only contain letters (A-Z, a-z), numerals (0-9), underscores (_), and hyphens (-).)
    print("Generated names:")
    for i in bucket_list:
        if i >= my_args.number:
            print(f"    (Skipped {i}, experiment only has {my_args.number} buckets)")
            continue
        print("    " + name_for(i, abbrev, my_args.exp, my_args.user, my_args.number))

    return 0
#####


###  Helpers  ###
def hash_exp(exp, name):
    hasher = hashlib.md5()
    hasher.update(exp.encode("utf-8"))
    hasher.update(name.encode("utf-8"))
    return hasher.hexdigest()


def bucket_int(hash):
    s = re.sub("[0-7]", "0", hash)
    s = re.sub("[8-9a-f]", "1", s)
    return int(s, 2)


def name_for(bucket, abbrev, exp, name, number):
    if abbrev:
        abbrev += "-"
    name_base = f"{name}-{abbrev}{bucket}-"
    for _ in range(100 * number):
        s = "".join(random.choices(string.digits + string.ascii_lowercase, k=5))  # NOTE: requires python 3.6+
        n = name_base + s
        b = bucket_int(hash_exp(exp, n)) % number
        if bucket == b:
            return n
    else:
        raise RuntimeError(f"Failed to generate a name for bucket {bucket} in {100 * number} tries")


def abbreviate(exp):
    "Deterministically creates a ~3-6 letter abbreviation, using initials and trying to stay as recognizable as possible"
    s = re.sub(r"[^0-9A-Za-z]+", "-", exp)  # drop symbols that aren't allowed in usernames (_ and - are allowed; this collapses them into -, simplifying some of the following)
    if len(re.findall(r"(^|[-])\w", s)) >= 3:
        # found at least a few word separators, use initials
        s = re.sub(r"(^|[-])(\w)[^-]*", r"\2", s).lower()
        s = re.sub(r"[-]", "", s)  # drop stray separators
    elif len(re.findall(r"[A-Z][^A-Z]+", s)) >= 3:
        # found at least a few capitalizations, use as initials, strip lowercase and junk
        s = re.sub(r"[a-z-]", "", s).lower()
    else:
        s = re.sub(r"[-]", "", s).lower()  # drop junk
        if len(s) > 6:
            # drop vowels except first & last and let the shortener trim it down from there
            s = s[0] + re.sub(r"[aeiou]", "", s[1:-1]) + s[-1]

    if len(s) > 6:
        # shorten abbreviation, keeping the beginning, middle, and last characters to preserve recognizability
        half = (len(s) - 1) // 2  # -1 to bias toward early-middle letters
        s = s[:2] + s[half - 1:half + 2] + s[-1:]
    return s
#####


#####
if __name__ == "__main__":
    import os, sys
    xit = main(sys.argv, os.environ)
    sys.exit(xit)
#####
