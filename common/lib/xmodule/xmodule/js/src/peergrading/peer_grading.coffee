# This is a simple class that just hides the error container
# and message container when they are empty
# Can (and should be) expanded upon when our problem list 
# becomes more sophisticated
class @PeerGrading

  peer_grading_sel: '.peer-grading'
  peer_grading_container_sel: '.peer-grading-container'
  error_container_sel: '.error-container'
  message_container_sel: '.message-container'
  problem_button_sel: '.problem-button'
  problem_list_sel: '.problem-list'
  progress_bar_sel: '.progress-bar'

  constructor: (element) ->
    @el = element
    @peer_grading_container = @$(@peer_grading_sel)
    @use_single_location = @peer_grading_container.data('use-single-location')
    @peer_grading_outer_container = @$(@peer_grading_container_sel)
    @ajax_url = @peer_grading_container.data('ajax-url')

    if @use_single_location.toLowerCase() == "true"
      #If the peer grading element is linked to a single location, then activate the backend for that location
      @activate_problem()
    else
      #Otherwise, activate the panel view.
      @error_container = @$(@error_container_sel)
      @error_container.toggle(not @error_container.is(':empty'))

      @message_container = @$(@message_container_sel)
      @message_container.toggle(not @message_container.is(':empty'))

      @problem_button = @$(@problem_button_sel)
      @problem_button.click @show_results

      @problem_list = @$(@problem_list_sel)
      @construct_progress_bar()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  construct_progress_bar: () =>
    problems = @problem_list.find('tr').next()
    problems.each( (index, element) =>
      problem = $(element)
      progress_bar = problem.find(@progress_bar_sel)
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
        backend = new PeerGradingProblemBackend(@ajax_url, false)
        new PeerGradingProblem(backend, @el)
      else
        @gentle_alert response.error

  activate_problem: () =>
    backend = new PeerGradingProblemBackend(@ajax_url, false)
    new PeerGradingProblem(backend, @el)