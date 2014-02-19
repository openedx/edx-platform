# wrap everything in a class in case we want to use inside xmodules later

get_random_int: (min, max) ->
  return Math.floor(Math.random() * (max - min + 1)) + min

# states
state_grading = "grading"
state_graded = "graded"
state_no_data = "no_data"
state_error = "error"

class @StaffGradingBackend
  constructor: (ajax_url, mock_backend) ->
    @ajax_url = ajax_url
    # prevent this from trying to make requests when we don't have
    # a proper url
    if !ajax_url
      mock_backend = true
    @mock_backend = mock_backend
    if @mock_backend
      @mock_cnt = 0

  mock: (cmd, data) ->
    # Return a mock response to cmd and data
    # should take a location as an argument
    if cmd == 'get_next'
      @mock_cnt++
      switch data.location
        when 'i4x://MITx/3.091x/problem/open_ended_demo1'
          response =
            success: true
            problem_name: 'Problem 1'
            num_graded: 3
            min_for_ml: 5
            num_pending: 4
            prompt: '''
            	<h2>S11E3: Metal Bands</h2>
<p>Shown below are schematic band diagrams for two different metals. Both diagrams appear different, yet both of the elements are undisputably metallic in nature.</p>
<img width="480" src="/static/images/LSQimages/shaded_metal_bands.png"/>
<p>* Why is it that both sodium and magnesium behave as metals, even though the s-band of magnesium is filled? </p>
<p>This is a self-assessed open response question. Please use as much space as you need in the box below to answer the question.</p>
            '''
            submission: '''
            Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of "de Finibus Bonorum et Malorum" (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, "Lorem ipsum dolor sit amet..", comes from a line in section 1.10.32.

The standard chunk of Lorem Ipsum used since the 1500s is reproduced below for those interested. Sections 1.10.32 and 1.10.33 from "de Finibus Bonorum et Malorum" by Cicero are also reproduced in their exact original form, accompanied by English versions from the 1914 translation by H. Rackham.
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
        </tr></tbody></table>'''
            submission_id: @mock_cnt
            max_score: 2 + @mock_cnt % 3
            ml_error_info : 'ML accuracy info: ' + @mock_cnt
        when 'i4x://MITx/3.091x/problem/open_ended_demo2'
          response =
            success: true
            problem_name: 'Problem 2'
            num_graded: 2
            min_for_ml: 5
            num_pending: 4
            prompt: 'This is a fake second problem'
            submission: 'This is the best submission ever! ' + @mock_cnt
            rubric: 'I am a rubric for grading things! ' + @mock_cnt
            submission_id: @mock_cnt
            max_score: 2 + @mock_cnt % 3
            ml_error_info : 'ML accuracy info: ' + @mock_cnt
        else
          response =
            success: false


    else if cmd == 'save_grade'
      response =
        @mock('get_next', {location: data.location})
    # get_problem_list
    # should get back a list of problem_ids, problem_names, num_graded, min_for_ml
    else if cmd == 'get_problem_list'
      @mock_cnt = 1
      response =
        success: true
        problem_list: [
          {location: 'i4x://MITx/3.091x/problem/open_ended_demo1', \
            problem_name: "Problem 1", num_graded: 3, num_pending: 5, min_for_ml: 10},
          {location: 'i4x://MITx/3.091x/problem/open_ended_demo2', \
            problem_name: "Problem 2", num_graded: 1, num_pending: 5, min_for_ml: 10}
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
        .error => callback({success: false, error: "Error occurred while performing javascript AJAX post."})


class @StaffGrading
  grading_message_sel: '.grading-message'

  constructor: (backend) ->
    AjaxPrefix.addAjaxPrefix(jQuery, -> "")
    @backend = backend

    # all the jquery selectors
    @el = $('.staff-grading')
    @problem_list_container = $('.problem-list-container')
    @problem_list = $('.problem-list')

    @error_container = $('.error-container')
    @message_container = $('.message-container')

    @prompt_name_container = $('.prompt-name')
    @prompt_container = $('.prompt-container')
    @prompt_wrapper = $('.prompt-wrapper')

    @submission_container = $('.submission-container')
    @submission_wrapper = $('.submission-wrapper')

    @grading_wrapper = $('.grading-wrapper')

    @feedback_area = $('.feedback-area')
    @score_selection_container = $('.score-selection-container')
    @grade_selection_container = $('.grade-selection-container')
    @flag_submission_checkbox = $('.flag-checkbox')

    @submit_button = $('.submit-button')
    @action_button = $('.action-button')
    @skip_button = $('.skip-button')

    @problem_meta_info = $('.problem-meta-info-container')
    @meta_info_wrapper = $('.meta-info-wrapper')
    @ml_error_info_container = $('.ml-error-info-container')

    @breadcrumbs = $('.breadcrumbs')


    $(window).keydown @keydown_handler
    $(window).keyup @keyup_handler
    @question_header = $('.question-header')
    @question_header.click @collapse_question
    @collapse_question()

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
    @location = ''
    @prompt_name = ''
    @min_for_ml = 0
    @num_graded = 0
    @num_pending = 0
    @score_lst = []
    @grade = null
    @is_ctrl = false

    @problems = null

    # action handlers
    @submit_button.click @submit
    # TODO: fix this to do something more intelligent
    @action_button.click @submit
    @skip_button.click @skip_and_get_next

    # send initial request automatically
    @get_problem_list()


  setup_score_selection: =>
    @score_selection_container.html(@rubric)
    $('input[class="score-selection"]').change => @graded_callback()
    @rub = new Rubric(@el)
    @rub.initialize(@location)

  graded_callback: () =>
   # show button if we have scores for all categories
    if @rub.check_complete()
      @state = state_graded
      @submit_button.show()

  keydown_handler: (event) =>
    #Previously, responses were submitted when hitting enter.  Add in a modifier that ensures that ctrl+enter is needed.
    if event.which == 17 && @is_ctrl==false
      @is_ctrl=true
    else if @is_ctrl==true && event.which == 13 && !@list_view && @rub.check_complete()
      @submit_and_get_next()

  keyup_handler: (event) =>
    #Handle keyup event when ctrl key is released
    if event.which == 17 && @is_ctrl==true
      @is_ctrl=false

  set_button_text: (text) =>
    @action_button.attr('value', text)

  ajax_callback: (response) =>
    # always clear out errors and messages on transition.
    @error_msg = ''
    @message = ''

    if response.success
      if response.problem_list
        @problems = response.problem_list
      else if response.submission
        @data_loaded(response)
      else
        @no_more(response.message)
    else
      @error(response.error)

    @render_view()
    @scroll_to_top()

  get_next_submission: (location) ->
    @location = location
    @list_view = false
    @backend.post('get_next', {location: location}, @ajax_callback)

  skip_and_get_next: () =>
    data =
      score: @rub.get_total_score()
      rubric_scores: @rub.get_score_list()
      feedback: @feedback_area.val()
      submission_id: @submission_id
      location: @location
      skipped: true
      submission_flagged: false
    @gentle_alert "Skipped the submission."
    @backend.post('save_grade', data, @ajax_callback)

  get_problem_list: () ->
    @list_view = true
    @render_view(true)
    @backend.post('get_problem_list', {}, @ajax_callback)

  submit_and_get_next: () ->
    data =
      score: @rub.get_total_score()
      rubric_scores: @rub.get_score_list()
      feedback: @feedback_area.val()
      submission_id: @submission_id
      location: @location
      submission_flagged: @flag_submission_checkbox.is(':checked')
    @gentle_alert gettext("Grades saved.  Fetching the next submission to grade.")
    @backend.post('save_grade', data, @ajax_callback)

  gentle_alert: (msg) =>
    @grading_message = $(@grading_message_sel)
    @grading_message.html("")
    @grading_message.fadeIn()
    @grading_message.html("<p>" + msg + "</p>")

  error: (msg) ->
    @error_msg = msg
    @state = state_error

  data_loaded: (response) ->
    @prompt = response.prompt
    @submission = response.submission
    @rubric = response.rubric
    @submission_id = response.submission_id
    @feedback_area.val('')
    @grade = null
    @max_score = response.max_score
    @ml_error_info=response.ml_error_info
    @prompt_name = response.problem_name
    @num_graded = response.num_graded
    @min_for_ml = response.min_for_ml
    @num_pending = response.num_pending
    @state = state_grading
    if not @max_score?
      @error("No max score specified for submission.")

  no_more: (message) ->
    @prompt = null
    @prompt_name = ''
    @num_graded = 0
    @min_for_ml = 0
    @submission = null
    @rubric = null
    @ml_error_info = null
    @submission_id = null
    @message = message
    @grade = null
    @max_score = 0
    @state = state_no_data

  render_view: (before_ajax) ->
    # clear the problem list and breadcrumbs
    @problem_list.html('''
        <tr>
            <th>''' + gettext("Problem Name") + '''</th>
            <th>''' + gettext("Graded") + '''</th>
            <th>''' + gettext("Available to Grade") + '''</th>
            <th>''' + gettext("Required") + '''</th>
            <th>''' + gettext("Progress") + '''</th>
        </tr>
    ''')
    @breadcrumbs.html('')
    @problem_list_container.toggle(@list_view)
    if @backend.mock_backend
      @message = @message + "<p>NOTE: Mocking backend.</p>"
    @message_container.html(@message)
    @error_container.html(@error_msg)
    @message_container.toggle(@message != "")
    @error_container.toggle(@error_msg != "")
    @flag_submission_checkbox.prop('checked', false)


    # only show the grading elements when we are not in list view or the state
    # is invalid
    show_grading_elements = !(@list_view || @state == state_error ||
      @state == state_no_data)
    @prompt_wrapper.toggle(show_grading_elements)
    @submission_wrapper.toggle(show_grading_elements)
    @grading_wrapper.toggle(show_grading_elements)
    @meta_info_wrapper.toggle(show_grading_elements)
    @action_button.hide()

    if before_ajax
      @scroll_to_top()
    else
      if @list_view
        @render_list()
      else
        @render_problem()

  problem_link:(problem) ->
    link = $('<a>').attr('href', "javascript:void(0)").append(
      "#{problem.problem_name}")
        .click =>
          @get_next_submission problem.location

  make_paragraphs: (text) ->
    paragraph_split = text.split(/\n\s*\n/)
    new_text = ''
    for paragraph in paragraph_split
      new_text += "<p>#{paragraph}</p>"
    return new_text

  render_list: () ->
    for problem in @problems
      problem_row = $('<tr>')
      problem_row.append($('<td class="problem-name">').append(@problem_link(problem)))
      problem_row.append($('<td>').append("#{problem.num_graded}"))
      problem_row.append($('<td>').append("#{problem.num_pending}"))
      problem_row.append($('<td>').append("#{problem.num_required}"))
      row_progress_bar = $('<div>').addClass('progress-bar')
      progress_value = parseInt(problem.num_graded)
      progress_max = parseInt(problem.num_required) + progress_value
      row_progress_bar.progressbar({value: progress_value, max: progress_max})
      problem_row.append($('<td>').append(row_progress_bar))
      @problem_list.append(problem_row)

  render_problem: () ->
    # make the view elements match the state.  Idempotent.
    show_submit_button = true
    show_action_button = true

    problem_list_link = $('<a>').attr('href', 'javascript:void(0);')
      .append("< " + gettext("Back to problem list"))
      .click => @get_problem_list()

    # set up the breadcrumbing
    @breadcrumbs.append(problem_list_link)


    if @state == state_error
      @set_button_text(gettext('Try loading again'))
      show_action_button = true

    else if @state == state_grading
      @ml_error_info_container.html(@ml_error_info)
      available = _.template(gettext("<%= num %> available "), {num: @num_pending})
      graded = _.template(gettext("<%= num %> graded "), {num: @num_graded})
      needed = _.template(gettext("<%= num %> more needed to start ML"),
        {num: Math.max(@min_for_ml - @num_graded, 0)})
      meta_list = $("<div>")
        .append("<div class='meta-info'>#{available}</div>")
        .append("<div class='meta-info'>#{graded}</div>")
        .append("<div class='meta-info'>#{needed}</div>")
      @problem_meta_info.html(meta_list)

      @prompt_container.html(@prompt)
      @prompt_name_container.html("#{@prompt_name}")
      @submission_container.html(@make_paragraphs(@submission))
      # no submit button until user picks grade.
      show_submit_button = false
      show_action_button = false

      @setup_score_selection()

    else if @state == state_graded
      @set_button_text(gettext('Submit'))
      show_action_button = false

    else if @state == state_no_data
      @message_container.html(@message)
      @set_button_text(gettext('Re-check for submissions'))

    else
      @error(_.template(gettext('System got into invalid state: <%= state %>'), {state: @state}))

    @submit_button.toggle(show_submit_button)
    @action_button.toggle(show_action_button)

  submit: (event) =>
    event.preventDefault()

    if @state == state_error
      @get_next_submission(@location)
    else if @state == state_graded
      @submit_and_get_next()
    else if @state == state_no_data
      @get_next_submission(@location)
    else
      @error(gettext('System got into invalid state for submission: ') + @state)

  collapse_question: () =>
    @prompt_container.slideToggle()
    @prompt_container.toggleClass('open')
    if @question_header.text() == gettext("(Hide)")
      Logger.log 'staff_grading_hide_question', {location: @location}
      new_text = gettext("(Show)")
    else
      Logger.log 'staff_grading_show_question', {location: @location}
      new_text = gettext("(Hide)")
    @question_header.text(new_text)

  scroll_to_top: () =>
    #This try/catch is needed because jasmine fails with it
    try
      $('html, body').animate({
                              scrollTop: $(".staff-grading").offset().top
                              }, 200)
    catch error
      console.log("Scrolling error.")



# for now, just create an instance and load it...
mock_backend = false
ajax_url = $('.staff-grading').data('ajax_url')
backend = new StaffGradingBackend(ajax_url, mock_backend)

$(document).ready(() -> new StaffGrading(backend))
