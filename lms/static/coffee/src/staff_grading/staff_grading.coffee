# wrap everything in a class in case we want to use inside xmodules later
class StaffGrading
  constructor: ->
    alert('hi!')

  load: ->
    alert('loading')

# for now, just create an instance and load it...
grading = new StaffGrading
$(document).ready(grading.load)
