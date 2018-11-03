from exceptions import ValidationError

class BaseChecker(object):
    """Base class for checking autograded cells for errors"""
    def check_cell(self, cell):
        """Should raise ValidationError if error found"""
        raise NotImplementedError()
    
    def finalize(self):
        """Called after last cell. Can check state and raise ValidationError"""
        pass
    

class ModuleNotFoundChecker(BaseChecker):
    """Checks for `ModuleNotFoundError`
    
    This error does not cause any notebook grading errors, but can cause a 
    student to get a 0 score, especially if the instructor imports a module
    within an assert section. Normally no feedback would be provided to the 
    student
    """
    def check_cell(self, cell):
        if cell.get('outputs'):
            output = cell['outputs']
            for output in cell['outputs']:
                if output.get('ename', '') == 'ModuleNotFoundError':
                    raise ValidationError(output['evalue'])




