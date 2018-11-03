
import os
import argparse

import container
import autograded_checkers as ac


def assign(nb_name):
    assigner = container.AssignContainer(nb_name)
    results = assigner.run()
    print(results)

def autograde(username, nb_name, gen_feedback):
    # Recreates Instructor NB Data in the gradebook db
    assign(nb_name)

    # Grades student results
    checkers = [ac.ModuleNotFoundChecker()]
    autograder = container.AutoGradeContainer(nb_name, username, gen_feedback,
            autograded_checkers=checkers)
    results = autograder.run()
    print(results)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--cmd', type=str, help='specify "assign" or "grade"',
        dest='cmd', required=True)
    parser.add_argument('--username', type=str, help='student username', 
        dest='username', required=False)
    parser.add_argument('--nbname', type=str, 
        help='name of notebook (with .ipynb ext)', dest='nbname', required=True)
    parser.add_argument('--generate_feedback', type=bool, 
        help='if True, generates student feedback in .html form', 
        dest='gen_feedback', default=True)

    args = parser.parse_args()
    
    if args.cmd == 'assign':
        assign(args.nbname)
    elif args.cmd == 'grade':
        autograde(args.username, args.nbname, args.gen_feedback)
    else:
        print("unrecognized args.cmd: {}".format(args.cmd))
    


     


