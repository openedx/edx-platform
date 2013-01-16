# This is a simple class that just hides the error container
# and message container when they are empty
# Can (and should be) expanded upon when our problem list 
# becomes more sophisticated
class PeerGrading
  constructor: () ->
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))

    @message_container = $('.message-container')
    @message_container.toggle(not @message_container.is(':empty'))
  
    @problem_list = $('.problem-list')
    @construct_progress_bar()

  construct_progress_bar: () =>
    problems = @problem_list.find('tr').next()
    problems.each( (index, element) =>
      problem = $(element)
      progress_bar = problem.find('.progress-bar')
      bar_value = parseInt(problem.data('graded'))
      bar_max = parseInt(problem.data('required'))
      progress_bar.progressbar({value: bar_value, max: bar_max})
    )
    

$(document).ready(() -> new PeerGrading())
