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
class @PeerGradingProblemBackend
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
        .error => callback({success: false, error: "Error occurred while performing this operation"})

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
                <table class="rubric"><tbody><tr><th>Purpose</th>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-0" value="0"><label for="score-0-0">No product</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-1" value="1"><label for="score-0-1">Unclear purpose or main idea</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-2" value="2"><label for="score-0-2">Communicates an identifiable purpose and/or main idea for an audience</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-3" value="3"><label for="score-0-3">Achieves a clear and distinct purpose for a targeted audience and communicates main ideas with effectively used techniques to introduce and represent ideas and insights</label>
                </td>
                </tr><tr><th>Organization</th>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-0" value="0"><label for="score-1-0">No product</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-1" value="1"><label for="score-1-1">Organization is unclear; introduction, body, and/or conclusion are underdeveloped, missing or confusing.</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-2" value="2"><label for="score-1-2">Organization is occasionally unclear; introduction, body or conclusion may be underdeveloped.</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-3" value="3"><label for="score-1-3">Organization is clear and easy to follow; introduction, body and conclusion are defined and aligned with purpose.</label>
                </td>
                </tr></tbody></table>
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
                <table class="rubric"><tbody><tr><th>Purpose</th>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-0" value="0"><label for="score-0-0">No product</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-1" value="1"><label for="score-0-1">Unclear purpose or main idea</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-2" value="2"><label for="score-0-2">Communicates an identifiable purpose and/or main idea for an audience</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-0" id="score-0-3" value="3"><label for="score-0-3">Achieves a clear and distinct purpose for a targeted audience and communicates main ideas with effectively used techniques to introduce and represent ideas and insights</label>
                </td>
                </tr><tr><th>Organization</th>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-0" value="0"><label for="score-1-0">No product</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-1" value="1"><label for="score-1-1">Organization is unclear; introduction, body, and/or conclusion are underdeveloped, missing or confusing.</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-2" value="2"><label for="score-1-2">Organization is occasionally unclear; introduction, body or conclusion may be underdeveloped.</label>
                </td>

                <td>
                <input type="radio" class="score-selection" name="score-selection-1" id="score-1-3" value="3"><label for="score-1-3">Organization is clear and easy to follow; introduction, body and conclusion are defined and aligned with purpose.</label>
                </td>
                </tr></tbody></table>
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

class @PeerGradingProblem

  prompt_wrapper_sel: '.prompt-wrapper'
  peer_grading_container_sel: '.peer-grading-container'
  submission_container_sel: '.submission-container'
  prompt_container_sel: '.prompt-container'
  rubric_container_sel: '.rubric-container'
  flag_student_container_sel: '.flag-student-container'
  calibration_panel_sel: '.calibration-panel'
  grading_panel_sel: '.grading-panel'
  content_panel_sel: '.content-panel'
  grading_message_sel: '.grading-message'
  question_header_sel: '.question-header'
  flag_submission_confirmation_sel: '.flag-submission-confirmation'
  flag_submission_confirmation_button_sel: '.flag-submission-confirmation-button'
  flag_submission_removal_button_sel: '.flag-submission-removal-button'
  grading_wrapper_sel: '.grading-wrapper'
  calibration_feedback_sel: '.calibration-feedback'
  interstitial_page_sel: '.interstitial-page'
  calibration_interstitial_page_sel: '.calibration-interstitial-page'
  error_container_sel: '.error-container'
  peer_grading_instructions_sel: '.peer-grading-instructions'
  feedback_area_sel: '.feedback-area'
  ice_legend_sel: '.ice-legend'
  score_selection_container_sel: '.score-selection-container'
  rubric_selection_container_sel: '.rubric-selection-container'
  submit_button_sel: '.submit-button'
  action_button_sel: '.action-button'
  calibration_feedback_button_sel: '.calibration-feedback-button'
  interstitial_page_button_sel: '.interstitial-page-button'
  calibration_interstitial_page_button_sel: '.calibration-interstitial-page-button'
  flag_checkbox_sel: '.flag-checkbox'
  calibration_text_sel: '.calibration-text'
  grading_text_sel: '.grading-text'
  calibration_feedback_wrapper_sel: '.calibration-feedback-wrapper'

  constructor: (backend, el) ->
    @el = el
    @prompt_wrapper = $(@prompt_wrapper_sel)
    @backend = backend
    @is_ctrl = false
    @el = $(@peer_grading_container_sel)

    # get the location of the problem
    @location = $('.peer-grading').data('location')
    # prevent this code from trying to run
    # when we don't have a location
    if(!@location)
      return

    # get the other elements we want to fill in
    @submission_container = @$(@submission_container_sel)
    @prompt_container = @$(@prompt_container_sel)
    @rubric_container = @$(@rubric_container_sel)
    @flag_student_container = @$(@flag_student_container_sel)
    @calibration_panel = @$(@calibration_panel_sel)
    @grading_panel = @$(@grading_panel_sel)
    @content_panel = @$(@content_panel_sel)
    @grading_message = @$(@grading_message_sel)
    @grading_message.hide()
    @question_header = @$(@question_header_sel)
    @question_header.click @collapse_question
    @flag_submission_confirmation = @$(@flag_submission_confirmation_sel)
    @flag_submission_confirmation_button = @$(@flag_submission_confirmation_button_sel)
    @flag_submission_removal_button = @$(@flag_submission_removal_button_sel)

    @flag_submission_confirmation_button.click @close_dialog_box
    @flag_submission_removal_button.click @remove_flag

    @grading_wrapper = @$(@grading_wrapper_sel)
    @calibration_feedback_panel = @$(@calibration_feedback_sel)
    @interstitial_page = @$(@interstitial_page_sel)
    @interstitial_page.hide()

    @calibration_interstitial_page = @$(@calibration_interstitial_page_sel)
    @calibration_interstitial_page.hide()

    @error_container = @$(@error_container_sel)

    @submission_key_input = $("input[name='submission-key']")
    @essay_id_input = @$("input[name='essay-id']")
    @peer_grading_instructions = @$(@peer_grading_instructions_sel)
    @feedback_area = @$(@feedback_area_sel)
    @ice_legend = @$(@ice_legend_sel)

    @score_selection_container = @$(@score_selection_container_sel)
    @rubric_selection_container = @$(@rubric_selection_container_sel)
    @grade = null
    @calibration = null

    @submit_button = @$(@submit_button_sel)
    @action_button = @$(@action_button_sel)
    @calibration_feedback_button = @$(@calibration_feedback_button_sel)
    @interstitial_page_button = @$(@interstitial_page_button_sel)
    @calibration_interstitial_page_button = @$(@calibration_interstitial_page_button_sel)
    @flag_student_checkbox = @$(@flag_checkbox_sel)

    $(window).keydown @keydown_handler
    $(window).keyup @keyup_handler

    Collapsible.setCollapsibles(@content_panel)

    # Set up the click event handlers
    @action_button.click -> history.back()
    @calibration_feedback_button.click =>
      @calibration_feedback_panel.hide()
      @grading_wrapper.show()
      @gentle_alert "Calibration essay saved.  Fetching the next essay."
      @is_calibrated_check()

    @interstitial_page_button.click =>
      @interstitial_page.hide()
      @is_calibrated_check()

    @calibration_interstitial_page_button.click =>
      @calibration_interstitial_page.hide()
      @is_calibrated_check()

    @flag_student_checkbox.click =>
      @flag_box_checked()

    @calibration_feedback_button.hide()
    @calibration_feedback_panel.hide()
    @error_container.hide()
    @flag_submission_confirmation.hide()

    if @tracking_changes()
      @change_tracker = new TrackChanges(@el)

    @is_calibrated_check()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)


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
    if @tracking_changes()
      feedback_content = @feedback_area.html()
    else
      feedback_content = @feedback_area.val()
    
    data =
      rubric_scores: @rub.get_score_list()
      score: @rub.get_total_score()
      location: @location
      submission_id: @essay_id_input.val()
      submission_key: @submission_key_input.val()
      feedback: feedback_content
      submission_flagged: @flag_student_checkbox.is(':checked')
      # hardcoding answer_unknown to false
      answer_unknown: false
    return data


  submit_calibration_essay: ()=>
    data = @construct_data()
    @submit_button.hide()
    @backend.post('save_calibration_essay', data, @calibration_callback)

  submit_grade: () =>
    data = @construct_data()
    @submit_button.hide()
    @backend.post('save_grade', data, @submission_callback)


  ##########
  #
  #  Callbacks for various events
  #
  ##########

  remove_flag: () =>
    @flag_student_checkbox.removeAttr("checked")
    @close_dialog_box()
    @submit_button.attr('disabled', true)

  close_dialog_box: () =>
    $(@flag_submission_confirmation_sel).dialog('close')

  flag_box_checked: () =>
    if @flag_student_checkbox.is(':checked')
      @$(@flag_submission_confirmation_sel).dialog({ height: 400, width: 400 })
      @submit_button.attr('disabled', false)

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
       else if not response.calibrated and @calibration==null
         @calibration=true
         @render_calibration_interstitial_page()
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
      message = "<p>Successfully saved your feedback. Fetching the next essay."
      if response.required_done
        message = message + " You have done the required number of peer assessments but may continue grading if you like."
      message = message + "</p>"
      @grading_message.html(message)
    else
      if response.error
        @render_error(response.error)
      else
        @render_error("Error occurred while submitting grade")

  # called after a grade is selected on the interface
  graded_callback: (event) =>
    ev = @$(event.target).parent().parent()
    ul = ev.parent().parent()
    ul.find(".rubric-label-selected").removeClass('rubric-label-selected')
    ev.addClass('rubric-label-selected')
    # check to see whether or not any categories have not been scored
    if @rub.check_complete()
      # show button if we have scores for all categories
      @grading_message.hide()
      @show_submit_button()
      @grade = @rub.get_total_score()

  keydown_handler: (event) =>
    #Previously, responses were submitted when hitting enter.  Add in a modifier that ensures that ctrl+enter is needed.
    if event.which == 17 && @is_ctrl==false
      @is_ctrl=true
    else if event.which == 13 && @submit_button.is(':visible') && @is_ctrl==true
      if @calibration
        @submit_calibration_essay()
      else
        @submit_grade()

  keyup_handler: (event) =>
    #Handle keyup event when ctrl key is released
    if event.which == 17 && @is_ctrl==true
      @is_ctrl=false


  ##########
  #
  #  Rendering methods and helpers
  #
  ##########
  # renders a calibration essay
  render_calibration: (response) =>
    if response.success

      # load in all the data
      @submission_container.html("")
      @render_submission_data(response)
      # TODO: indicate that we're in calibration mode
      @calibration_panel.addClass('current-state')
      @grading_panel.removeClass('current-state')

      # Display the right text
      # both versions of the text are written into the template itself
      # we only need to show/hide the correct ones at the correct time
      @calibration_panel.find(@calibration_text_sel).show()
      @grading_panel.find(@calibration_text_sel).show()
      @calibration_panel.find(@grading_text_sel).hide()
      @grading_panel.find(@grading_text_sel).hide()
      @flag_student_container.hide()
      @peer_grading_instructions.hide()
      @feedback_area.attr('disabled', true)
      feedback_text = "Once you are done learning to grade, and are grading your peers' work, you will be asked to share written feedback with them in addition to scoring them."
      if @tracking_changes()
        @ice_legend.hide()
        @feedback_area.attr('contenteditable', false)
        @feedback_area.text(feedback_text)
      else
        @feedback_area.val(feedback_text)
      @submit_button.show()
      @submit_button.unbind('click')
      @submit_button.click @submit_calibration_essay
      @submit_button.attr('disabled', true)
      @scroll_to_top()
    else if response.error
      @render_error(response.error)
    else
      @render_error("An error occurred while retrieving the next calibration essay")

  tracking_changes: () =>
    return @grading_wrapper.data('track-changes') == true

  # Renders a student submission to be graded
  render_submission: (response) =>
    if response.success
      @submit_button.hide()
      @submission_container.html("")
      @render_submission_data(response)

      @calibration_panel.removeClass('current-state')
      @grading_panel.addClass('current-state')

      # Display the correct text
      # both versions of the text are written into the template itself
      # we only need to show/hide the correct ones at the correct time
      @calibration_panel.find(@calibration_text_sel).hide()
      @grading_panel.find(@calibration_text_sel).hide()
      @calibration_panel.find(@grading_text_sel).show()
      @grading_panel.find(@grading_text_sel).show()
      @flag_student_container.show()
      @peer_grading_instructions.show()
      if @tracking_changes()
        @ice_legend.show()
        @feedback_area.html(@make_paragraphs(response.student_response))
        @change_tracker.rebindTracker()
      else
        @feedback_area.val("")
      @feedback_area.attr('disabled', false)
      @flag_student_checkbox.removeAttr("checked")
      @submit_button.show()
      @submit_button.unbind('click')
      @submit_button.click @submit_grade
      @submit_button.attr('disabled', true)
      @scroll_to_top()
    else if response.error
      @render_error(response.error)
    else
      @render_error("An error occurred when retrieving the next submission.")

  make_paragraphs: (text) ->
    paragraph_split = text.split(/\n\s*\n/)
    new_text = ''
    for paragraph in paragraph_split
      new_text += "<p>#{paragraph}</p>"
    return new_text

  # render common information between calibration and grading
  render_submission_data: (response) =>
    @content_panel.show()
    @error_container.hide()

    @submission_container.append(@make_paragraphs(response.student_response))
    @prompt_container.html(response.prompt)
    @rubric_selection_container.html(response.rubric)
    @submission_key_input.val(response.submission_key)
    @essay_id_input.val(response.submission_id)
    @setup_score_selection(response.max_score)

    @submit_button.hide()
    @action_button.hide()
    @calibration_feedback_panel.hide()
    @rub = new Rubric(@el)
    @rub.initialize(@location)


  render_calibration_feedback: (response) =>
    # display correct grade
    @calibration_feedback_panel.slideDown()
    calibration_wrapper = @$(@calibration_feedback_wrapper_sel)
    calibration_wrapper.html("<p>The score you gave was: #{@grade}. The instructor score is: #{response.actual_score}</p>")

    score = parseInt(@grade)
    actual_score = parseInt(response.actual_score)

    if score == actual_score
      calibration_wrapper.append("<p>Your score matches the instructor score!</p>")
    else
      calibration_wrapper.append("<p>You may want to review the rubric again.</p>")

    if response.actual_rubric != undefined
      calibration_wrapper.append("<div>Instructor Scored Rubric: #{response.actual_rubric}</div>")
    if response.actual_feedback.feedback!=undefined
      calibration_wrapper.append("<div>Instructor Feedback: #{response.actual_feedback}</div>")

    # disable score selection and submission from the grading interface
    @$("input[name='score-selection']").attr('disabled', true)
    @submit_button.hide()
    @calibration_feedback_button.show()

  render_interstitial_page: () =>
    @content_panel.hide()
    @grading_message.hide()
    @interstitial_page.show()

  render_calibration_interstitial_page: () =>
    @content_panel.hide()
    @action_button.hide()
    @calibration_interstitial_page.show()

  render_error: (error_message) =>
      @error_container.show()
      @calibration_feedback_panel.hide()
      @error_container.html(error_message)
      @content_panel.hide()
      @action_button.show()

  show_submit_button: () =>
    @submit_button.attr('disabled', false)
    @submit_button.show()

  setup_score_selection: (max_score) =>
    # And now hook up an event handler again
    @$("input[class='score-selection']").change @graded_callback

  gentle_alert: (msg) =>
    @grading_message.fadeIn()
    @grading_message.html("<p>" + msg + "</p>")

  collapse_question: (event) =>
    @prompt_container.slideToggle()
    @prompt_container.toggleClass('open')
    if @question_header.text() == "Hide Question"
      new_text = "Show Question"
      Logger.log 'oe_hide_question', {location: @location}
    else
      Logger.log 'oe_show_question', {location: @location}
      new_text = "Hide Question"
    @question_header.text(new_text)
    return false

  scroll_to_top: () =>
    $('html, body').animate({
                            scrollTop: $(".peer-grading").offset().top
                            }, 200)
