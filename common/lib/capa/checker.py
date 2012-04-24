#!/usr/bin/env python
"""
Commandline tool for doing operations on Problems
"""
import argparse
import logging
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

    args = parser.parse_args()
    log.setLevel(logging.INFO)

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
    answers = problem.get_question_answers()
    log.debug(answers)
    if answers:
        try:
            results = problem.grade_answers(answers)
            log.debug(results)
            assert(all(result == 'correct' for result in results.values()))
        except AssertionError:
            log.error("The following generated answers were not accepted:")
            for question_id, result in sorted(results.items()):
                if result != 'correct':
                    log.error("  {0} = {1}".format(question_id, answers[question_id]))
        except Exception as ex:
            log.exception(ex)



if __name__ == '__main__':
    sys.exit(main())
