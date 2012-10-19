from calc import evaluator, UndefinedVariable

#-----------------------------------------------------------------------------
#
# Utility functions used in CAPA responsetypes


def compare_with_tolerance(v1, v2, tol):
    ''' Compare v1 to v2 with maximum tolerance tol
    tol is relative if it ends in %; otherwise, it is absolute

     - v1    :  student result (number)
     - v2    :  instructor result (number)
     - tol   :  tolerance (string representing a number)

    '''
    relative = tol.endswith('%')
    if relative:
        tolerance_rel = evaluator(dict(), dict(), tol[:-1]) * 0.01
        tolerance = tolerance_rel * max(abs(v1), abs(v2))
    else:
        tolerance = evaluator(dict(), dict(), tol)
    return abs(v1 - v2) <= tolerance


def contextualize_text(text, context):  # private
    ''' Takes a string with variables. E.g. $a+$b.
    Does a substitution of those variables from the context '''
    if not text: return text
    for key in sorted(context, lambda x, y: cmp(len(y), len(x))):
        # TODO (vshnayder): This whole replacement thing is a big hack
        # right now--context contains not just just the vars defined
        # in the program, but also e.g. a reference to the numpy
        # module.  Should be a separate dict of variables that are
        # should be replaced.
        if '$' + key in text:
            try:
                s = str(context[key])
            except UnicodeEncodeError:
                s = context[key].encode('utf8', errors='ignore')
            text = text.replace('$' + key, s)
    return text


def convert_files_to_filenames(answers):
    '''
    Check for File objects in the dict of submitted answers,
        convert File objects to their filename (string)
    '''
    new_answers = dict()
    for answer_id in answers.keys():
        answer = answers[answer_id]
        if is_list_of_files(answer): # Files are stored as a list, even if one file
            new_answers[answer_id] = [f.name for f in answer]
        else:
            new_answers[answer_id] = answers[answer_id]
    return new_answers

def is_list_of_files(files):
    return isinstance(files, list) and all(is_file(f) for f in files)

def is_file(file_to_test):
    '''
    Duck typing to check if 'file_to_test' is a File object
    '''
    return all(hasattr(file_to_test, method) for method in ['read', 'name'])
