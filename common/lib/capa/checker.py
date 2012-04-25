#!/usr/bin/env python
"""
Commandline tool for doing operations on Problems
"""
import argparse
import logging
import os.path
import sys

from cStringIO import StringIO

from capa_problem import LoncapaProblem

logging.basicConfig(format="%(levelname)s %(message)s")
log = logging.getLogger('capa.checker')

def main():
    parser = argparse.ArgumentParser(description='Check Problem Files')
    parser.add_argument("command", choices=['test']) # Watch? Render? Open?
    parser.add_argument("files", nargs="+", type=argparse.FileType('r'))
    parser.add_argument("--seed", required=False, type=int)
    parser.add_argument("--log-level", required=False, default="INFO",
                        choices=['info', 'debug', 'warn', 'error',
                                 'INFO', 'DEBUG', 'WARN', 'ERROR'])

    args = parser.parse_args()
    log.setLevel(args.log_level.upper())

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    for problem_file in args.files:
        log.info("Opening {0}".format(problem_file.name))
        sys.stdout = problem_stdout = StringIO()
        sys.stderr = problem_stderr = StringIO()

        try:
            problem = LoncapaProblem(problem_file.name, "fakeid", seed=args.seed)
        except Exception as ex:
            log.error("Could not parse file {0}".format(problem_file.name))
            log.exception(ex)
            continue

        if args.command == 'test':
            test_problem(problem)
            log_captured_output(problem_stdout, 
                                "captured stdout from {0}".format(problem_file.name))
            log_captured_output(problem_stderr,
                                "captured stderr from {0}".format(problem_file.name))

        # Print captured problem prints
        problem_file.close()

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    # In case we want to do anything else here.

def log_captured_output(output_stream, stream_name):
    output_stream.seek(0)
    output_text = output_stream.read()
    if output_text:
        log.info("##### Begin {0} #####\n".format(stream_name) + output_text)
        log.info("##### End {0} #####".format(stream_name))

def test_problem(problem):
    """Split this up so that we're only used for formula/numeric answers.

    Examples of where this fails:
    * Displayed answers use units but acceptable ones do not.
      - L1e0.xml
      - Presents itself as UndefinedVariable (when it tries to pass to calc)
    * "a or d" is what's displayed, but only "a" or "d" is accepted, not the 
      string "a or d".
      - L1-e00.xml
    """
    # These are actual answers we get from the responsetypes
    real_answers = problem.get_question_answers()

    # all_answers is real_answers + blanks for other answer_ids for which the
    # responsetypes can't provide us pre-canned answers (customresopnse)
    all_answer_ids = problem.get_answer_ids()
    all_answers = dict((answer_id, real_answers.get(answer_id, ""))
                       for answer_id in all_answer_ids)

    log.debug(real_answers)
    if real_answers:
        try:
            real_results = dict((answer_id, result) for answer_id, result 
                                in problem.grade_answers(all_answers).items()
                                if answer_id in real_answers)
            log.debug(real_results)
            assert(all(result == 'correct'
                       for answer_id, result in real_results.items()))
        except AssertionError:
            log.error("The following generated answers were not accepted:")
            for question_id, result in sorted(real_results.items()):
                if result != 'correct':
                    log.error("  {0} = {1}".format(question_id, real_answers[question_id]))
        except Exception as ex:
            log.exception(ex)



if __name__ == '__main__':
    sys.exit(main())
