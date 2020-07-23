from .constants import XBLOCKS_EXCEPT_PROBLEM, date_format


def get_due_date_for_problem_xblock(due, module_category):
    """
    :param due: It's due date of sub section
    :param module_category: category of the xblock
    :return: formatted due date for xblocks that are problem type
    and for other xblocks it's None
    """
    due_date = None

    if module_category not in XBLOCKS_EXCEPT_PROBLEM:
        if due:
            due_date = due.strftime(date_format)

    return due_date
