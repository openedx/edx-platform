# wrap everything in a class in case we want to use inside xmodules later

get_random_int: (min, max) ->
  return Math.floor(Math.random() * (max - min + 1)) + min

# states
state_grading = "grading"
state_graded = "graded"
state_no_data = "no_data"
state_error = "error"

class StaffGradingBackend
  constructor: (ajax_url, mock_backend) ->
    @ajax_url = ajax_url
    @mock_backend = mock_backend
    if @mock_backend
      @mock_cnt = 0

  mock: (cmd, data) ->
    # Return a mock response to cmd and data
    # should take a problem id as an argument
    if cmd == 'get_next'
      @mock_cnt++
      response =
        success: true
        problem_name: 'Problem 1'
        num_left: 3
        num_total: 5
        prompt: 'This is a fake prompt'
        submission: 'submission! ' + @mock_cnt
        rubric: 'A rubric! ' + @mock_cnt
        submission_id: @mock_cnt
        max_score: 2 + @mock_cnt % 3
        ml_error_info : 'ML error info!' + @mock_cnt

    else if cmd == 'save_grade'
      console.log("eval: #{data.score} pts,  Feedback: #{data.feedback}")
      response =
        @mock('get_next', {})
    # get_probblem_list
    # sends in a course_id and a grader_id
    # should get back a list of problem_ids, problem_names, num_left, num_total
    else if cmd == 'get_problem_list'
        response = 
            success: true
            problem_list: [
                {problem_id: 1, problem_name: "Problem 1", num_left: 3, num_total: 5}
                {problem_id: 2, problem_name: "Problem 2", num_left: 1, num_total: 5}
            ]
    else
      response =
        success: false
        error: 'Unknown command ' + cmd

    if @mock_cnt % 5 == 0
        response = 
          success: true
          message: 'No more submissions'


    if @mock_cnt % 7 == 0
      response =
        success: false
        error: 'An error for testing'
        
    return response


  post: (cmd, data, callback) ->
    if @mock_backend
      callback(@mock(cmd, data))
    else
      # TODO: replace with postWithPrefix when that's loaded
      $.post(@ajax_url + cmd, data, callback)


class StaffGrading
  constructor: (backend) ->
    @backend = backend

    # all the jquery selectors
    @error_container = $('.error-container')
    @message_container = $('.message-container')

    @prompt_container = $('.prompt-container')
    @prompt_wrapper = $('.prompt-wrapper')

    @submission_container = $('.submission-container')
    @submission_wrapper = $('.submission-wrapper')

    @rubric_container = $('.rubric-container')
    @rubric_wrapper = $('.rubric-wrapper')

    @feedback_area = $('.feedback-area')
    @score_selection_container = $('.score-selection-container')        
    @submit_button = $('.submit-button')
    @ml_error_info_container = $('.ml-error-info-container')
    
    # model state
    @state = state_no_data
    @submission_id = null
    @prompt = ''
    @submission = ''
    @rubric = ''
    @error_msg = ''
    @message = ''
    @max_score = 0
    @ml_error_info= ''

    @score = null

    # action handlers
    @submit_button.click @submit

    # render intial state
    @render_view()

    # send initial request automatically
    @get_next_submission()


  setup_score_selection: =>
    # first, get rid of all the old inputs, if any.
    @score_selection_container.html('Choose score: ')

    # Now create new labels and inputs for each possible score.
    for score in [0..@max_score]
      id = 'score-' + score
      label = """<label for="#{id}">#{score}</label>"""
      
      input = """
              <input type="radio" name="score-selection" id="#{id}" value="#{score}"/>
              """       # "  fix broken parsing in emacs
      @score_selection_container.append(input + label)

    # And now hook up an event handler again
    $("input[name='score-selection']").change @graded_callback
    

  set_button_text: (text) =>
    @submit_button.attr('value', text)

  graded_callback: (event) =>
    @score = event.target.value
    @state = state_graded
    @render_view()

  ajax_callback: (response) =>
    # always clear out errors and messages on transition.
    @error_msg = ''
    @message = ''
    
    if response.success
      if response.submission
        @data_loaded(response.prompt, response.submission, response.rubric, response.submission_id, response.max_score, response.ml_error_info)
      else
        @no_more(response.message)
    else
      @error(response.error)

    @render_view()
       
  get_next_submission: () ->
    @backend.post('get_next', {}, @ajax_callback)

  submit_and_get_next: () ->
    data =
      score: @score
      feedback: @feedback_area.val()
      submission_id: @submission_id
    
    @backend.post('save_grade', data, @ajax_callback)

  error: (msg) ->
    @error_msg = msg
    @state = state_error

  data_loaded: (prompt, submission, rubric, submission_id, max_score, ml_error_info) ->
    @prompt = prompt
    @submission = submission
    @rubric = rubric
    @submission_id = submission_id
    @feedback_area.val('')
    @max_score = max_score
    @score = null
    @ml_error_info=ml_error_info
    @state = state_grading
    if not @max_score?
      @error("No max score specified for submission.")

  no_more: (message) ->
    @prompt = null
    @submission = null
    @rubric = null
    @ml_error_info = null
    @submission_id = null
    @message = message
    @score = null
    @max_score = 0
    @state = state_no_data

  render_view: () ->
    # make the view elements match the state.  Idempotent.
    show_grading_elements = false
    show_submit_button = true

    @message_container.html(@message)
    if @backend.mock_backend
      @message_container.append("<p>NOTE: Mocking backend.</p>")
    
    @error_container.html(@error_msg)

    if @state == state_error
      @set_button_text('Try loading again')

    else if @state == state_grading
      @ml_error_info_container.html(@ml_error_info)
      @prompt_container.html(@prompt)
      @submission_container.html(@submission)
      @rubric_container.html(@rubric)
      show_grading_elements = true

      # no submit button until user picks grade.
      show_submit_button = false

      @setup_score_selection()
      
    else if @state == state_graded
      show_grading_elements = true
      @set_button_text('Submit')

    else if @state == state_no_data
      @message_container.html(@message)
      @set_button_text('Re-check for submissions')

    else
      @error('System got into invalid state ' + @state)

    @submit_button.toggle(show_submit_button)
    @prompt_wrapper.toggle(show_grading_elements)
    @submission_wrapper.toggle(show_grading_elements)
    @rubric_wrapper.toggle(show_grading_elements)
    @ml_error_info_container.toggle(show_grading_elements)


  submit: (event) =>
    event.preventDefault()
    
    if @state == state_error
      @get_next_submission()
    else if @state == state_graded
      @submit_and_get_next()
    else if @state == state_no_data
      @get_next_submission()
    else
      @error('System got into invalid state for submission: ' + @state)
  

# for now, just create an instance and load it...
mock_backend = false
ajax_url = $('.staff-grading').data('ajax_url')
backend = new StaffGradingBackend(ajax_url, mock_backend)

$(document).ready(() -> new StaffGrading(backend))
