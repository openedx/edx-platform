class PeerGradingProblemBackend
  constructor: (ajax_url, mock_backend) ->
    @mock_backend = mock_backend
    @ajax_url = ajax_url

  post: (cmd, data, callback) ->
    if @mock_backend
      callback(@mock(cmd, data))
    else
      # TODO: replace with postWithPrefix when that's loaded
      $.post(@ajax_url + cmd, data, callback)
        .error => callback({success: false, error: "Error occured while performing this operation"})

  mock: (cmd, data) ->
    if cmd == 'is_student_calibrated'
      # change to test each version
      response = 
        success: true 
        calibrated: false
    else if cmd == 'show_calibration_essay'
      response = 
        success: true
        submission_id: 1
        submission_key: 'abcd'
        student_response: 'I am a fake response'
        prompt: 'Answer this question'
        rubric: 'This is a rubric.'
        max_score: 4

        
    return response


class PeerGradingProblem
  constructor: (backend) ->
    @prompt_wrapper = $('.prompt-wrapper')
    @backend = backend
    
    # ugly hack to prevent this code from trying to run on the
    # general peer grading page
    if( @prompt_wrapper.length == 0)
      return

    # get the location of the problem
    @location = $('.peer-grading').data('location')

    # get the other elements we want to fill in
    @submission_container = $('.submission-container')
    @prompt_container = $('.prompt-container')
    @rubric_container = $('.rubric-container')

    @error_container = $('.error-container')

    @is_calibrated_check()


  is_calibrated_check: () =>
    @backend.post('is_student_calibrated', {}, @calibration_check_callback)


  fetch_calibration_essay: ()=>
    @backend.post('show_calibration_essay', {location: @location}, @render_calibration)

  render_calibration: (response) =>
    if response.success
      #TODO: fill this in

      @submission_container.html("<h3>Calibration Essay</h3>")
      @submission_container.append(response.student_response)
      @prompt_container.html(response.prompt)
      @rubric_container.html(response.rubric)

    else
      @error_container.show()
      @error_container.html(response.error)

  render_submission: (response) ->
    #TODO: fill this in

  calibration_check_callback: (response) =>
    if response.success
      # check whether or not we're still calibrating
       if response.calibrated
         @fetch_submission()
         @calibration = false
       else
         @fetch_calibration_essay()
         @calibration = true




mock_backend = true
ajax_url = $('.peer-grading').data('ajax_url')
backend = new PeerGradingProblemBackend(ajax_url, mock_backend)
$(document).ready(() -> new PeerGradingProblem(backend))
