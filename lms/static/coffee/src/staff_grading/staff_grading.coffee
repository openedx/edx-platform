# wrap everything in a class in case we want to use inside xmodules later

get_random_int: (min, max) ->
  return Math.floor(Math.random() * (max - min + 1)) + min

# states
state_grading = "have_data"
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
    @mock_cnt++
    if cmd == 'get_next'
      response =
        success: true
        submission: 'submission! ' + @mock_cnt
        rubric: 'A rubric!' + @mock_cnt

    else if cmd == 'save_grade'
      response =
        success: true
        submission: 'another submission! ' + @mock_cnt
        rubric: 'A rubric!' + @mock_cnt
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

    @error_container = $('.error-container')
    @message_container = $('.message-container')
    @submission_container = $('.submission-container')
    @rubric_container = $('.rubric-container')
    @submission_wrapper = $('.submission-wrapper')
    @rubric_wrapper = $('.rubric-wrapper')
    @button = $('.submit-button')
    @button.click @clicked
    @state = state_no_data

    @submission_wrapper.hide()
    @rubric_wrapper.hide()

    @get_next_submission()


  set_button_text: (text) ->
    @button.prop('value', text)


  ajax_callback: (response) =>
      if response.success
        if response.submission
          @data_loaded(response.submission, response.rubric)
        else
          @no_more()
      else
        @error(response.error)
  
  get_next_submission: () ->
    @backend.post('get_next', {}, @ajax_callback)

  submit_and_get_next: () ->
    data = {eval: '123'}
    @backend.post('save_grade', data, @ajax_callback)

  error: (msg) ->
    @error_container.html(msg)
    @state = state_error
    @update()

  data_loaded: (submission, rubric) ->
    @submission_container.html(submission)
    @rubric_container.html(rubric)
    @state = state_grading
    @update()

  no_more: () ->
    @state = state_no_data
    @update()

  update: () ->
    # make button and div state match the state.  Idempotent.
    if @state == state_error
      @set_button_text('Try loading again')

    else if @state == state_grading
      @submission_wrapper.show()
      @rubric_wrapper.show()
      @set_button_text('Submit')

    else if @state == state_no_data
      @submission_wrapper.hide()
      @rubric_wrapper.hide()
      @message_container.html('Nothing to grade')
      @set_button_text('Re-check for submissions')

    else
      @error('System got into invalid state ' + @state)

  clicked: (event) =>
    event.preventDefault()
    # always clear out errors and messages on transition...
    @message_container.html('')
    @error_container.html('')

    if @state == state_error
      @get_next_submission()
    else if @state == state_grading
      @submit_and_get_next()
    else if @state == state_no_data
      @get_next_submission()
    else
      @error('System got into invalid state ' + @state)
  

# for now, just create an instance and load it...
mock_backend = true
ajax_url = $('.staff-grading').data('ajax_url')
backend = new StaffGradingBackend(ajax_url, mock_backend)

$(document).ready(() -> new StaffGrading(backend))
