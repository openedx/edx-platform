# This is a simple class that just hides the error container
# and message container when they are empty
# Can (and should be) expanded upon when our problem list 
# becomes more sophisticated
class PeerGrading
  constructor: () ->
    @peer_grading_container = $('.peer-grading')
    @peer_grading_outer_container = $('.peer-grading-container')
    @ajax_url = peer_grading_container.data('ajax-url')
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))

    @message_container = $('.message-container')
    @message_container.toggle(not @message_container.is(':empty'))

    @problem_button = $('.problem-button')
    @problem_button.click show_results

    @problem_list = $('.problem-list')
    @construct_progress_bar()

  construct_progress_bar: () =>
    problems = @problem_list.find('tr').next()
    problems.each( (index, element) =>
      problem = $(element)
      progress_bar = problem.find('.progress-bar')
      bar_value = parseInt(problem.data('graded'))
      bar_max = parseInt(problem.data('required')) + bar_value
      progress_bar.progressbar({value: bar_value, max: bar_max})
    )

  show_results: (event) =>
    location_to_fetch = $(event.target).data('location')
    data = {'location' : location_to_fetch}
    $.postWithPrefix "#{@ajax_url}problem", data, (response) =>
      if response.success
        @peer_grading_outer_container.after(response.html).remove()
      else
        @gentle_alert response.error

$(document).ready(() -> new PeerGrading())
