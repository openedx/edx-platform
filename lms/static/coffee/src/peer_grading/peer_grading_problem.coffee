##################################
#
#  This is the JS that renders the peer grading problem page.
#  Fetches the correct problem and/or calibration essay
#  and sends back the grades
#
#  Should not be run when we don't have a location to send back
#  to the server
#
#  PeerGradingProblemBackend - 
#   makes all the ajax requests and provides a mock interface
#   for testing purposes
#
#  PeerGradingProblem -
#   handles the rendering and user interactions with the interface
#
##################################
class PeerGradingProblemBackend
  constructor: (ajax_url, mock_backend) ->
    @mock_backend = mock_backend
    @ajax_url = ajax_url
    @mock_cnt = 0

  post: (cmd, data, callback) ->
    if @mock_backend
      callback(@mock(cmd, data))
    else
      # if this post request fails, the error callback will catch it
      $.post(@ajax_url + cmd, data, callback)
        .error => callback({success: false, error: "Error occured while performing this operation"})

  mock: (cmd, data) ->
    if cmd == 'is_student_calibrated'
      # change to test each version
      response = 
        success: true 
        calibrated: @mock_cnt >= 2
    else if cmd == 'show_calibration_essay'
      #response = 
      #  success: false
      #  error: "There was an error"
      @mock_cnt++
      response = 
        success: true
        submission_id: 1
        submission_key: 'abcd'
        student_response: '''
            Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of "de Finibus Bonorum et Malorum" (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, "Lorem ipsum dolor sit amet..", comes from a line in section 1.10.32.

The standard chunk of Lorem Ipsum used since the 1500s is reproduced below for those interested. Sections 1.10.32 and 1.10.33 from "de Finibus Bonorum et Malorum" by Cicero are also reproduced in their exact original form, accompanied by English versions from the 1914 translation by H. Rackham.
            '''
        prompt: '''
            	<h2>S11E3: Metal Bands</h2>
<p>Shown below are schematic band diagrams for two different metals. Both diagrams appear different, yet both of the elements are undisputably metallic in nature.</p>
<p>* Why is it that both sodium and magnesium behave as metals, even though the s-band of magnesium is filled? </p>
<p>This is a self-assessed open response question. Please use as much space as you need in the box below to answer the question.</p>
            '''
        rubric: '''
<ul>
<li>Metals tend to be good electronic conductors, meaning that they have a large number of electrons which are able to access empty (mobile) energy states within the material.</li>
<li>Sodium has a half-filled s-band, so there are a number of empty states immediately above the highest occupied energy levels within the band.</li>
<li>Magnesium has a full s-band, but the the s-band and p-band overlap in magnesium. Thus are still a large number of available energy states immediately above the s-band highest occupied energy level.</li>
</ul>

<p>Please score your response according to how many of the above components you identified:</p>
            '''
        max_score: 4
    else if cmd == 'get_next_submission'
      response = 
        success: true
        submission_id: 1
        submission_key: 'abcd'
        student_response: '''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed nec tristique ante. Proin at mauris sapien, quis varius leo. Morbi laoreet leo nisi. Morbi aliquam lacus ante. Cras iaculis velit sed diam mattis a fermentum urna luctus. Duis consectetur nunc vitae felis facilisis eget vulputate risus viverra. Cras consectetur ullamcorper lobortis. Nam eu gravida lorem. Nulla facilisi. Nullam quis felis enim. Mauris orci lectus, dictum id cursus in, vulputate in massa.

Phasellus non varius sem. Nullam commodo lacinia odio sit amet egestas. Donec ullamcorper sapien sagittis arcu volutpat placerat. Phasellus ut pretium ante. Nam dictum pulvinar nibh dapibus tristique. Sed at tellus mi, fringilla convallis justo. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus tristique rutrum nulla sed eleifend. Praesent at nunc arcu. Mauris condimentum faucibus nibh, eget commodo quam viverra sed. Morbi in tincidunt dolor. Morbi sed augue et augue interdum fermentum.

Curabitur tristique purus ac arcu consequat cursus. Cras diam felis, dignissim quis placerat at, aliquet ac metus. Mauris vulputate est eu nibh imperdiet varius. Cras aliquet rhoncus elit a laoreet. Mauris consectetur erat et erat scelerisque eu faucibus dolor consequat. Nam adipiscing sagittis nisl, eu mollis massa tempor ac. Nulla scelerisque tempus blandit. Phasellus ac ipsum eros, id posuere arcu. Nullam non sapien arcu. Vivamus sit amet lorem justo, ac tempus turpis. Suspendisse pharetra gravida imperdiet. Pellentesque lacinia mi eu elit luctus pellentesque. Sed accumsan libero a magna elementum varius. Nunc eget pellentesque metus. '''
        prompt: '''
            	<h2>S11E3: Metal Bands</h2>
<p>Shown below are schematic band diagrams for two different metals. Both diagrams appear different, yet both of the elements are undisputably metallic in nature.</p>
<p>* Why is it that both sodium and magnesium behave as metals, even though the s-band of magnesium is filled? </p>
<p>This is a self-assessed open response question. Please use as much space as you need in the box below to answer the question.</p>
            '''
        rubric: '''
<ul>
<li>Metals tend to be good electronic conductors, meaning that they have a large number of electrons which are able to access empty (mobile) energy states within the material.</li>
<li>Sodium has a half-filled s-band, so there are a number of empty states immediately above the highest occupied energy levels within the band.</li>
<li>Magnesium has a full s-band, but the the s-band and p-band overlap in magnesium. Thus are still a large number of available energy states immediately above the s-band highest occupied energy level.</li>
</ul>

<p>Please score your response according to how many of the above components you identified:</p>
            '''
        max_score: 4
    else if cmd == 'save_calibration_essay'
      response = 
        success: true
        actual_score: 2
    else if cmd == 'save_grade'
      response = 
        success: true

    return response


class PeerGradingProblem
  constructor: (backend) ->
    @prompt_wrapper = $('.prompt-wrapper')
    @backend = backend
    

    # get the location of the problem
    @location = $('.peer-grading').data('location')
    # prevent this code from trying to run 
    # when we don't have a location
    if(!@location)
      return

    # get the other elements we want to fill in
    @submission_container = $('.submission-container')
    @prompt_container = $('.prompt-container')
    @rubric_container = $('.rubric-container')
    @calibration_panel = $('.calibration-panel')
    @grading_panel = $('.grading-panel')
    @content_panel = $('.content-panel')
    @grading_message = $('.grading-message')
    @grading_message.hide()

    @grading_wrapper =$('.grading-wrapper')
    @calibration_feedback_panel = $('.calibration-feedback')
    @interstitial_page = $('.interstitial-page')
    @interstitial_page.hide()

    @error_container = $('.error-container')

    @submission_key_input = $("input[name='submission-key']")
    @essay_id_input = $("input[name='essay-id']")
    @feedback_area = $('.feedback-area')

    @score_selection_container = $('.score-selection-container')
    @score = null
    @calibration = null

    @submit_button = $('.submit-button')
    @action_button = $('.action-button')
    @calibration_feedback_button = $('.calibration-feedback-button')
    @interstitial_page_button = $('.interstitial-page-button')

    Collapsible.setCollapsibles(@content_panel)

    # Set up the click event handlers
    @action_button.click -> history.back()
    @calibration_feedback_button.click => 
      @calibration_feedback_panel.hide()
      @grading_wrapper.show()
      @is_calibrated_check()

    @interstitial_page_button.click =>
      @interstitial_page.hide()
      @is_calibrated_check()

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

  construct_data: () ->
    data =
      score: @score
      location: @location
      submission_id: @essay_id_input.val()
      submission_key: @submission_key_input.val()
      feedback: @feedback_area.val() 
    return data


  submit_calibration_essay: ()=>
    data = @construct_data()
    @backend.post('save_calibration_essay', data, @calibration_callback)

  submit_grade: () =>
    data = @construct_data()
    @backend.post('save_grade', data, @submission_callback)
    

  ##########
  #
  #  Callbacks for various events
  #
  ##########

  # called after we perform an is_student_calibrated check
  calibration_check_callback: (response) =>
    if response.success
      # if we haven't been calibrating before
       if response.calibrated and (@calibration == null or @calibration == false)
         @calibration = false
         @fetch_submission_essay()
      # If we were calibrating before and no longer need to,
      # show the interstitial page
       else if response.calibrated and @calibration == true
         @calibration = false
         @render_interstitial_page()
       else
         @calibration = true
         @fetch_calibration_essay()
    else if response.error
      @render_error(response.error)
    else
      @render_error("Error contacting the grading service")


  # called after we submit a calibration score
  calibration_callback: (response) =>
    if response.success
      @render_calibration_feedback(response)
    else if response.error
      @render_error(response.error)
    else 
      @render_error("Error saving calibration score")

  # called after we submit a submission score
  submission_callback: (response) =>
    if response.success
      @is_calibrated_check()
      @grading_message.fadeIn()
      @grading_message.html("<p>Grade sent successfully.</p>")
    else
      if response.error
        @render_error(response.error)
      else
        @render_error("Error occurred while submitting grade")

  # called after a grade is selected on the interface
  graded_callback: (event) =>
    @grading_message.hide()
    @score = event.target.value
    @show_submit_button()

  
      
  ##########
  #
  #  Rendering methods and helpers
  #
  ##########
  # renders a calibration essay
  render_calibration: (response) =>
    if response.success

      # load in all the data
      @submission_container.html("<h3>Training Essay</h3>")
      @render_submission_data(response)
      # TODO: indicate that we're in calibration mode 
      @calibration_panel.addClass('current-state')
      @grading_panel.removeClass('current-state')

      # Display the right text
      # both versions of the text are written into the template itself
      # we only need to show/hide the correct ones at the correct time
      @calibration_panel.find('.calibration-text').show()
      @grading_panel.find('.calibration-text').show()
      @calibration_panel.find('.grading-text').hide()
      @grading_panel.find('.grading-text').hide()


      @submit_button.unbind('click')
      @submit_button.click @submit_calibration_essay

    else if response.error
      @render_error(response.error)
    else
      @render_error("An error occurred while retrieving the next calibration essay")

  # Renders a student submission to be graded
  render_submission: (response) =>
    if response.success
      @submit_button.hide()
      @submission_container.html("<h3>Submitted Essay</h3>")
      @render_submission_data(response)

      @calibration_panel.removeClass('current-state')
      @grading_panel.addClass('current-state')

      # Display the correct text
      # both versions of the text are written into the template itself
      # we only need to show/hide the correct ones at the correct time
      @calibration_panel.find('.calibration-text').hide()
      @grading_panel.find('.calibration-text').hide()
      @calibration_panel.find('.grading-text').show()
      @grading_panel.find('.grading-text').show()

      @submit_button.unbind('click')
      @submit_button.click @submit_grade
    else if response.error
      @render_error(response.error)
    else
      @render_error("An error occured when retrieving the next submission.")


  make_paragraphs: (text) ->
    paragraph_split = text.split(/\n\s*\n/)
    new_text = ''
    for paragraph in paragraph_split
      new_text += "<p>#{paragraph}</p>"
    return new_text

  # render common information between calibration and grading
  render_submission_data: (response) =>
    @content_panel.show()

    @submission_container.append(@make_paragraphs(response.student_response))
    @prompt_container.html(response.prompt)
    @rubric_container.html(response.rubric)
    @submission_key_input.val(response.submission_key)
    @essay_id_input.val(response.submission_id)
    @setup_score_selection(response.max_score)

    @submit_button.hide()
    @action_button.hide()
    @calibration_feedback_panel.hide()


  render_calibration_feedback: (response) =>
    # display correct grade
    @calibration_feedback_panel.slideDown()
    calibration_wrapper = $('.calibration-feedback-wrapper')
    calibration_wrapper.html("<p>The score you gave was: #{@score}. The actual score is: #{response.actual_score}</p>")


    score = parseInt(@score)
    actual_score = parseInt(response.actual_score)

    if score == actual_score
      calibration_wrapper.append("<p>Congratulations! Your score matches the actual score!</p>")
    else
      calibration_wrapper.append("<p>Please try to understand the grading critera better to be more accurate next time.</p>") 

    # disable score selection and submission from the grading interface
    $("input[name='score-selection']").attr('disabled', true)
    @submit_button.hide()
    
  render_interstitial_page: () =>
    @content_panel.hide()
    @interstitial_page.show()

  render_error: (error_message) =>
      @error_container.show()
      @calibration_feedback_panel.hide()
      @error_container.html(error_message)
      @content_panel.hide()
      @action_button.show()

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



mock_backend = false
ajax_url = $('.peer-grading').data('ajax_url')
backend = new PeerGradingProblemBackend(ajax_url, mock_backend)
$(document).ready(() -> new PeerGradingProblem(backend))
