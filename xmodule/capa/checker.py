#!/usr/bin/env python
"""
Commandline tool for doing operations on Problems
"""

import argparse
import logging
import sys
from io import BytesIO

from calc import UndefinedVariable
from django.template.loader import get_template

from xmodule.capa.capa_problem import LoncapaProblem

logging.basicConfig(format="%(levelname)s %(message)s")
log = logging.getLogger("capa.checker")


class DemoSystem:  # pylint: disable=too-few-public-methods
    """Render templates using Django's template engine."""

    def __init__(self):
        self.DEBUG = True  # pylint: disable=invalid-name

    def render_template(self, template_filename, dictionary):
        """
        Render the specified template with the given dictionary of context data.
        """
        return get_template(template_filename).render(dictionary)


def main():
    """Parse command-line arguments to test or display Loncapa problem files."""

    parser = argparse.ArgumentParser(description="Check Problem Files")
    parser.add_argument("command", choices=["test", "show"])  # Watch? Render? Open?
    parser.add_argument("files", nargs="+", type=argparse.FileType("r"))
    parser.add_argument("--seed", required=False, type=int)
    parser.add_argument(
        "--log-level",
        required=False,
        default="INFO",
        choices=["info", "debug", "warn", "error", "INFO", "DEBUG", "WARN", "ERROR"],
    )

    args = parser.parse_args()
    log.setLevel(args.log_level.upper())

    system = DemoSystem()

    for problem_file in args.files:
        log.info("Opening %s", problem_file.name)

        try:
            problem = LoncapaProblem(  # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
                problem_file,
                "fakeid",
                seed=args.seed,
                system=system,
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.error("Could not parse file %s", problem_file.name)
            log.exception(ex)
            continue

        if args.command == "test":
            command_test(problem)
        elif args.command == "show":
            command_show(problem)

        problem_file.close()

    # In case we want to do anything else here.


def command_show(problem):
    """Display the text for this problem"""
    print(problem.get_html())


def command_test(problem):
    """Run tests on a problem while capturing and logging stdout and stderr output."""

    # We're going to trap stdout/stderr from the problems (yes, some print)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout = BytesIO()
        sys.stderr = BytesIO()

        check_that_suggested_answers_work(problem)
        check_that_blanks_fail(problem)

        log_captured_output(sys.stdout, f"captured stdout from {problem}")
        log_captured_output(sys.stderr, f"captured stderr from {problem}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.exception(e)
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


def check_that_blanks_fail(problem):
    """Leaving it blank should never work. Neither should a space."""
    blank_answers = dict((answer_id, "") for answer_id in problem.get_question_answers())
    grading_results = problem.grade_answers(blank_answers)
    try:
        assert all(result == "incorrect" for result in grading_results.values())
    except AssertionError:
        log.error(
            "Blank accepted as correct answer in %s for %s",
            problem,
            [answer_id for answer_id, result in sorted(grading_results.items()) if result != "incorrect"],
        )


def check_that_suggested_answers_work(problem):
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
    # responsetypes can't provide us pre-canned answers (customresponse)
    all_answer_ids = problem.get_answer_ids()
    all_answers = dict((answer_id, real_answers.get(answer_id, "")) for answer_id in all_answer_ids)

    log.debug("Real answers: %s", real_answers)
    if real_answers:
        try:
            real_results = dict(
                (answer_id, result)
                for answer_id, result in problem.grade_answers(all_answers).items()
                if answer_id in real_answers
            )
            log.debug(real_results)
            assert all(result == "correct" for answer_id, result in real_results.items())
        except UndefinedVariable as uv_exc:
            log.error(
                'The variable "%s" specified in the solution isn\'t recognized (is it a units measure?).',
                uv_exc,
            )
        except AssertionError:
            log.error("The following generated answers were not accepted for %s:", problem)
            for question_id, result in sorted(real_results.items()):
                if result != "correct":
                    log.error("  %s = %s", question_id, real_answers[question_id])
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.error("Uncaught error in %s", problem)
            log.exception(ex)


def log_captured_output(output_stream, stream_name):
    """Log the contents of a captured output stream with header and footer markers."""

    output_stream.seek(0)
    output_text = output_stream.read()
    if output_text:
        log.info("##### Begin %s #####\n%s", stream_name, output_text)
        log.info("##### End %s #####", stream_name)


if __name__ == "__main__":
    sys.exit(main())
