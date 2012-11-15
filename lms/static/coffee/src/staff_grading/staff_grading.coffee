# wrap everything in a class in case we want to use inside xmodules later
class StaffGrading
  constructor: ->
    @submission_container = $('.submission-container')
    @rubric_container = $('.rubric-container')
    @submit_button = $('.submit-button')
    @mock_backend = true

    @load()

    
  load: ->
    alert('loading')

# for now, just create an instance and load it...
$(document).ready(() -> new StaffGrading)
