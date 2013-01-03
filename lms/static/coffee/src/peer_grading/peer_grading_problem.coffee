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
      #response = 
      #  success: false
      #  error: "There was an error"
      response = 
        success: true
        submission_id: 1
        submission_key: 'abcd'
        student_response: 'I am a fake calibration response'
        prompt: 'Answer this question'
        rubric: 'This is a rubric.'
        max_score: 4
    else if cmd == 'get_next_submission'
      response = 
        success: true
        submission_id: 1
        submission_key: 'abcd'
        student_response: 'I am a fake student response'
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
    @instructions_panel = $('.instructions-panel')
    @content_panel = $('.content-panel')

    @error_container = $('.error-container')

    @submission_key_input = $("input[name='submission-key']")
    @essay_id_input = $("input[name='essay-id']")

    @score_selection_container = $('.score-selection-container')
    @score = null

    @submit_button = $('.submit-button')
    @action_button = $('.action-button')

    @action_button.click -> document.location.reload(true)

    @is_calibrated_check()


  ##########
  #
  #  Ajax calls to the backend
  #
  ##########
  is_calibrated_check: () =>
    @backend.post('is_student_calibrated', {location: @location}, @calibration_check_callback)

  fetch_calibration_essay: () =>
    @backend.post('show_calibration_essay', {location: @location}, @render_calibration)

  fetch_submission_essay: () =>
    @backend.post('get_next_submission', {location: @location}, @render_submission)

  submit_calibration_essay: ()->
    #TODO: onclick of the submit button. submits the calibration essay grade

  submit_grade: () ->
    #TODO: onclick of the submit button. submits the grade
    

  ##########
  #
  #  Callbacks for various events
  #
  ##########
  calibration_check_callback: (response) =>
    if response.success
      # check whether or not we're still calibrating
       if response.calibrated
         @fetch_submission()
         @calibration = false
       else
         @fetch_calibration_essay()
         @calibration = true
    else if response.error
      @render_error(response.error)
    else
      @render_error("Error contacting the grading service")


  submission_callback: (response) =>
    if response.success
      @is_calibrated_check()
    else
      if response.error
        @render_error(response.error)
      else
        @render_error("Error occurred while submitting grade")

  graded_callback: (event) =>
    @score = event.target.value
    @show_submit_button()

  
      
  ##########
  #
  #  Rendering methods and helpers
  #
  ##########
  render_calibration: (response) =>
    if response.success

      # load in all the data
      @submission_container.html("<h3>Calibration Essay</h3>")
      @render_submission_data(response)

      # TODO: indicate that we're in calibration mode 

    else
      if response.error
        @render_error(response.error)
      else
        @render_error("An error occurred while contacting the grading server")

  render_submission_data: (response) =>
    @content_panel.show()
    @submission_container.append(response.student_response)
    @prompt_container.html(response.prompt)
    @rubric_container.html(response.rubric)
    @submission_key_input.val(response.submission_key)
    @essay_id_input.val(response.submission_id)
    @setup_score_selection(response.max_score)
    @submit_button.hide()
    @action_button.hide()


  render_submission: (response) =>
    #TODO: fill this in
    @submit_button.hide()
    @render_submission_data(response)
    
  render_error: (error_message) =>
      @error_container.show()
      @error_container.html(error_message)
      @content_panel.hide()

  show_submit_button: () =>
    @submit_button.show()

  setup_score_selection: (max_score) =>
    # first, get rid of all the old inputs, if any.
    @score_selection_container.html('Choose score: ')

    # Now create new labels and inputs for each possible score.
    for score in [0..max_score]
      id = 'score-' + score
      label = """<label for="#{id}">#{score}</label>"""
      
      input = """
              <input type="radio" name="score-selection" id="#{id}" value="#{score}"/>
              """       # "  fix broken parsing in emacs
      @score_selection_container.append(input + label)

    # And now hook up an event handler again
    $("input[name='score-selection']").change @graded_callback





mock_backend = true
ajax_url = $('.peer-grading').data('ajax_url')
backend = new PeerGradingProblemBackend(ajax_url, mock_backend)
$(document).ready(() -> new PeerGradingProblem(backend))
