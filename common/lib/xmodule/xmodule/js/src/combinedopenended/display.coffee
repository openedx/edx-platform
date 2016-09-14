class @Rubric

  rubric_category_sel: '.rubric-category'
  rubric_sel: '.rubric'

  constructor: (el) ->
    @el = el

  initialize: (location) =>
    @$(@rubric_sel).data("location", location)
    @$('input[class="score-selection"]').change @tracking_callback
    # set up the hotkeys
    $(window).unbind('keydown', @keypress_callback)
    $(window).keydown @keypress_callback
    # display the 'current' carat
    @categories = @$(@rubric_category_sel)
    @category = @$(@categories.first())
    @category_index = 0

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  keypress_callback: (event) =>
    # don't try to do this when user is typing in a text input
    if @$(event.target).is('input, textarea')
      return
    # for when we select via top row
    if event.which >= 48 and event.which <= 57
      selected = event.which - 48
    # for when we select via numpad
    else if event.which >= 96 and event.which <= 105
      selected = event.which - 96
    # we don't want to do anything since we haven't pressed a number
    else
      return

    # if we actually have a current category (not past the end)
    if(@category_index <= @categories.length)
      # find the valid selections for this category
      inputs = @$("input[name='score-selection-#{@category_index}']")
      max_score = inputs.length - 1

      if selected > max_score or selected < 0
        return
      inputs.filter("input[value=#{selected}]").click()

      @category_index++
      @category = @$(@categories[@category_index])
    
  tracking_callback: (event) =>
    target_selection = @$(event.target).val()
    # chop off the beginning of the name so that we can get the number of the category
    category = @$(event.target).data("category")
    location = @$(@rubric_sel).data('location')
    # probably want the original problem location as well

    data = {location: location, selection: target_selection, category: category}
    Logger.log 'rubric_select', data

  # finds the scores for each rubric category
  get_score_list: () =>
    # find the number of categories:
    num_categories = @$(@rubric_category_sel).length

    score_lst = []
    # get the score for each one
    for i in [0..(num_categories-1)]
      score = @$("input[name='score-selection-#{i}']:checked").val()
      score_lst.push(score)

    return score_lst

  get_total_score: () =>
    score_lst = @get_score_list()
    tot = 0
    for score in score_lst
      tot += parseInt(score)
    return tot

  check_complete: () =>
     # check to see whether or not any categories have not been scored
    num_categories = @$(@rubric_category_sel).length
    for i in [0..(num_categories-1)]
      score = @$("input[name='score-selection-#{i}']:checked").val()
      if score == undefined
        return false
    return true

class @CombinedOpenEnded

  wrapper_sel: 'section.xmodule_CombinedOpenEndedModule'
  coe_sel: 'section.combined-open-ended'
  reset_button_sel: '.reset-button'
  next_step_sel: '.next-step-button'
  question_header_sel: '.question-header'
  submit_evaluation_sel: '.submit-evaluation-button'
  result_container_sel: 'div.result-container'
  combined_rubric_sel: '.combined-rubric-container'
  open_ended_child_sel: 'section.open-ended-child'
  error_sel: '.error'
  answer_area_sel: 'textarea.answer'
  answer_area_div_sel : 'div.answer'
  prompt_sel: '.prompt'
  rubric_wrapper_sel: '.rubric-wrapper'
  hint_wrapper_sel: '.hint-wrapper'
  message_wrapper_sel: '.message-wrapper'
  submit_button_sel: '.submit-button'
  skip_button_sel: '.skip-button'
  file_upload_sel: '.file-upload'
  file_upload_box_sel: '.file-upload-box'
  file_upload_preview_sel: '.file-upload-preview'
  fof_sel: 'textarea.feedback-on-feedback'
  sub_id_sel: 'input.submission_id'
  grader_id_sel: 'input.grader_id'
  grader_status_sel: '.grader-status'
  info_rubric_elements_sel: '.rubric-info-item'
  rubric_collapse_sel: '.rubric-collapse'
  next_rubric_sel: '.rubric-next-button'
  previous_rubric_sel: '.rubric-previous-button'
  oe_alert_sel: '.open-ended-alert'
  save_button_sel: '.save-button'

  constructor: (el) ->
    @el=el
    @$el = $(el)
    @reinitialize(el)
    $(window).keydown @keydown_handler
    $(window).keyup @keyup_handler

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  reinitialize: () ->
    @has_been_reset = false
    @wrapper=@$(@wrapper_sel)
    @coe = @$(@coe_sel)

    @ajax_url = @coe.data('ajax-url')
    @get_html()
    @coe = @$(@coe_sel)

    #Get data from combinedopenended
    @allow_reset = @coe.data('allow_reset')
    @id = @coe.data('id')
    @state = @coe.data('state')
    @task_count = @coe.data('task-count')
    @task_number = @coe.data('task-number')
    @accept_file_upload = @coe.data('accept-file-upload')
    @location = @coe.data('location')

    # set up handlers for click tracking
    @rub = new Rubric(@coe)
    @rub.initialize(@location)
    @is_ctrl = false

    #Setup reset
    @reset_button = @$(@reset_button_sel)
    @reset_button.click @confirm_reset
    
    #Setup next problem
    @next_problem_button = @$(@next_step_sel)
    @next_problem_button.click @next_problem

    @question_header = @$(@question_header_sel)
    @question_header.click @collapse_question

    # valid states: 'initial', 'assessing', 'post_assessment', 'done'
    Collapsible.setCollapsibles(@$el)
    @submit_evaluation_button = @$(@submit_evaluation_sel)
    @submit_evaluation_button.click @message_post

    @results_container = @$(@result_container_sel)
    @combined_rubric_container = @$(@combined_rubric_sel)

    # Where to put the rubric once we load it
    @oe = @$(@open_ended_child_sel)

    @errors_area = @$(@oe).find(@error_sel)
    @answer_area = @$(@oe).find(@answer_area_sel)
    @prompt_container = @$(@oe).find(@prompt_sel)
    @rubric_wrapper = @$(@oe).find(@rubric_wrapper_sel)
    @hint_wrapper = @$(@oe).find(@hint_wrapper_sel)
    @message_wrapper = @$(@oe).find(@message_wrapper_sel)
    @submit_button = @$(@oe).find(@submit_button_sel)
    @save_button = @$(@oe).find(@save_button_sel)
    @child_state = @oe.data('state')
    @child_type = @oe.data('child-type')
    if @child_type=="openended"
      @skip_button = @$(@oe).find(@skip_button_sel)
      @skip_button.click @skip_post_assessment

    @file_upload_area = @$(@oe).find(@file_upload_sel)
    @can_upload_files = false
    @open_ended_child= @$(@oe).find(@open_ended_child_sel)

    @out_of_sync_message = 'The problem state got out of sync.  Try reloading the page.'

    if @task_number>1
      @prompt_hide()
    else if @task_number==1 and @child_state!='initial'
      @prompt_hide()

    @find_assessment_elements()
    @find_hint_elements()

    @rebind()

  get_html_callback: (response) =>
    @coe.replaceWith(response.html)

  get_html: () =>
    url = "#{@ajax_url}/get_html"
    $.ajaxWithPrefix({
                   type: 'POST',
                   url: url,
                   data: {},
                   success: @get_html_callback,
                   async:false
                   });

  show_combined_rubric_current: () =>
    data = {}
    $.postWithPrefix "#{@ajax_url}/get_combined_rubric", data, (response) =>
      if response.success
        @combined_rubric_container.after(response.html).remove()
        @combined_rubric_container= @$(@combined_rubric_sel)
        @toggle_rubric("")
        @rubric_collapse = @$(@rubric_collapse_sel)
        @rubric_collapse.click @toggle_rubric
        @hide_rubrics()
        @$(@previous_rubric_sel).click @previous_rubric
        @$(@next_rubric_sel).click @next_rubric
        if response.hide_reset
          @reset_button.hide()

  message_post: (event)=>
    external_grader_message=$(event.target).parent().parent().parent()
    evaluation_scoring = $(event.target).parent()

    fd = new FormData()
    feedback = @$(evaluation_scoring).find(@fof_sel)[0].value
    submission_id = @$(external_grader_message).find(@sub_id_sel)[0].value
    grader_id = @$(external_grader_message).find(@grader_id_sel)[0].value
    score = @$(evaluation_scoring).find("input:radio[name='evaluation-score']:checked").val()

    fd.append('feedback', feedback)
    fd.append('submission_id', submission_id)
    fd.append('grader_id', grader_id)
    if(!score)
      ###
      Translators: A "rating" is a score a student gives to indicate how well
      they feel they were graded on this problem
      ###
      @gentle_alert gettext "You need to pick a rating before you can submit."
      return
    else
      fd.append('score', score)

    settings =
      type: "POST"
      data: fd
      processData: false
      contentType: false
      success: (response) =>
        @gentle_alert response.msg
        @$('section.evaluation').slideToggle()
        @message_wrapper.html(response.message_html)


    $.ajaxWithPrefix("#{@ajax_url}/save_post_assessment", settings)


  rebind: () =>
    # rebind to the appropriate function for the current state
    @submit_button.unbind('click')
    @submit_button.show()
    @save_button.unbind('click')
    @save_button.hide()
    @reset_button.hide()
    @hide_file_upload()
    @next_problem_button.hide()
    @hint_area.attr('disabled', false)

    if @task_number==1 and @child_state=='assessing'
      @prompt_hide()
    if @child_state == 'done'
      @rubric_wrapper.hide()
    if @child_type=="openended"
      @skip_button.hide()
    if @allow_reset=="True"
      @show_combined_rubric_current()
      @reset_button.show()
      @submit_button.hide()
      @answer_area.attr("disabled", true)
      @replace_text_inputs()
      @hint_area.attr('disabled', true)
      if @task_number<@task_count
        ###
        Translators: this message appears when transitioning between openended grading
        types (i.e. self assesment to peer assessment). Sometimes, if a student
        did not perform well at one step, they cannot move on to the next one.
        ###
        @gentle_alert gettext "Your score did not meet the criteria to move to the next step."
    else if @child_state == 'initial'
      @answer_area.attr("disabled", false)
      @submit_button.prop('value', gettext 'Submit')
      @submit_button.click @confirm_save_answer
      @setup_file_upload()
      @save_button.click @store_answer
      @save_button.show()
    else if @child_state == 'assessing'
      @answer_area.attr("disabled", true)
      @replace_text_inputs()
      @hide_file_upload()
      ###
      Translators: one clicks this button after one has finished filling out the grading
      form for an openended assessment
      ###
      @submit_button.prop('value', gettext 'Submit assessment')
      @submit_button.click @save_assessment
      @submit_button.attr("disabled",true)
      if @child_type == "openended"
        @submit_button.hide()
        @queueing()
        @grader_status = @$(@grader_status_sel)
        @grader_status.html("<span class='grading'>" + (gettext "Your response has been submitted. Please check back later for your grade.") + "</span>")
      else if @child_type == "selfassessment"
        @setup_score_selection()
    else if @child_state == 'post_assessment'
      if @child_type=="openended"
        @skip_button.show()
        @skip_post_assessment()
      @answer_area.attr("disabled", true)
      @replace_text_inputs()
      ###
      Translators: this button is clicked to submit a student's rating of
      an evaluator's assessment
      ###
      @submit_button.prop('value', gettext 'Submit post-assessment')
      if @child_type=="selfassessment"
         @submit_button.click @save_hint
      else
        @submit_button.click @message_post
    else if @child_state == 'done'
      @show_combined_rubric_current()
      @rubric_wrapper.hide()
      @answer_area.attr("disabled", true)
      @replace_text_inputs()
      @hint_area.attr('disabled', true)
      @submit_button.hide()
      if @child_type=="openended"
        @skip_button.hide()
      if @task_number<@task_count
        @next_problem_button.show()
      else
        @reset_button.show()

  find_assessment_elements: ->
    @assessment = @$('input[name="grade-selection"]')

  find_hint_elements: ->
    @hint_area = @$('textarea.post_assessment')

  store_answer:  (event) =>
    event.preventDefault()
    if @child_state == 'initial'
      data = {'student_answer' : @answer_area.val()}
      @save_button.attr("disabled",true)
      $.postWithPrefix "#{@ajax_url}/store_answer", data, (response) =>
        if response.success
          @gentle_alert(gettext "Answer saved, but not yet submitted.")
        else
          @errors_area.html(response.error)
        @save_button.attr("disabled",false)
    else
      @errors_area.html(@out_of_sync_message)

  replace_answer: (response) =>
    if response.success
      @rubric_wrapper.html(response.rubric_html)
      @rubric_wrapper.show()
      @rub = new Rubric(@coe)
      @rub.initialize(@location)
      @child_state = 'assessing'
      @find_assessment_elements()
      @answer_area.val(response.student_response)
      @rebind()
      answer_area_div = @$(@answer_area_div_sel)
      answer_area_div.html(response.student_response)
    else
      @submit_button.show()
      @submit_button.attr('disabled', false)
      @gentle_alert response.error

  confirm_save_answer: (event) =>
    ###
    Translators: This string appears in a confirmation box after one tries to submit
    an openended problem
    ###
    confirmation_text = gettext 'Please confirm that you wish to submit your work. You will not be able to make any changes after submitting.' 
    accessible_confirm confirmation_text, =>
      @save_answer(event)

  save_answer: (event) =>
    @$el.find(@oe_alert_sel).remove()
    @submit_button.attr("disabled",true)
    @submit_button.hide()
    event.preventDefault()
    @answer_area.attr("disabled", true)
    max_filesize = 2*1000*1000 #2MB
    if @child_state == 'initial'
      files = ""
      valid_files_attached = false
      if @can_upload_files == true
        files = @$(@file_upload_box_sel)[0].files[0]
        if files != undefined
          valid_files_attached = true
          if files.size > max_filesize
            files = ""
            # Don't submit the file in the case of it being too large, deal with the error locally.
            @submit_button.show()
            @submit_button.attr('disabled', false)
            @gentle_alert gettext "You are trying to upload a file that is too large for our system.  Please choose a file under 2MB or paste a link to it into the answer box."
            return

      fd = new FormData()
      fd.append('student_answer', @answer_area.val())
      fd.append('student_file', files)
      fd.append('valid_files_attached', valid_files_attached)

      that=this
      settings =
        type: "POST"
        data: fd
        processData: false
        contentType: false
        async: false
        success: (response) =>
          @replace_answer(response)

      $.ajaxWithPrefix("#{@ajax_url}/save_answer",settings)
    else
      @errors_area.html(@out_of_sync_message)

  keydown_handler: (event) =>
    # Previously, responses were submitted when hitting enter.  Add in a modifier that ensures that ctrl+enter is needed.
    if event.which == 17 && @is_ctrl==false
      @is_ctrl=true
    else if @is_ctrl==true && event.which == 13 && @child_state == 'assessing' && @rub.check_complete()
      @save_assessment(event)

  keyup_handler: (event) =>
    # Handle keyup event when ctrl key is released
    if event.which == 17 && @is_ctrl==true
      @is_ctrl=false

  save_assessment: (event) =>
    @submit_button.attr("disabled",true)
    @submit_button.hide()
    event.preventDefault()
    if @child_state == 'assessing' && @rub.check_complete()
      checked_assessment = @rub.get_total_score()
      score_list = @rub.get_score_list()
      data = {'assessment' : checked_assessment, 'score_list' : score_list}
      $.postWithPrefix "#{@ajax_url}/save_assessment", data, (response) =>
        if response.success
          @child_state = response.state

          if @child_state == 'post_assessment'
            @hint_wrapper.html(response.hint_html)
            @find_hint_elements()
          else if @child_state == 'done'
            @rubric_wrapper.hide()

          @rebind()
        else
          @gentle_alert response.error
    else
      @errors_area.html(@out_of_sync_message)

  save_hint:  (event) =>
    event.preventDefault()
    if @child_state == 'post_assessment'
      data = {'hint' : @hint_area.val()}

      $.postWithPrefix "#{@ajax_url}/save_post_assessment", data, (response) =>
        if response.success
          @message_wrapper.html(response.message_html)
          @child_state = 'done'
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html(@out_of_sync_message)

  skip_post_assessment: =>
    if @child_state == 'post_assessment'

      $.postWithPrefix "#{@ajax_url}/skip_post_assessment", {}, (response) =>
        if response.success
          @child_state = 'done'
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html(@out_of_sync_message)

  confirm_reset: (event) =>
    message = gettext 'Are you sure you want to remove your previous response to this question?'
    accessible_confirm message, =>
      @reset(event)

  reset: (event) =>
    event.preventDefault()
    if @child_state == 'done' or @allow_reset=="True"
      $.postWithPrefix "#{@ajax_url}/reset", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @coe.after(response.html).remove()
          @allow_reset="False"
          @reinitialize(@element)
          @has_been_reset = true
          @rebind()
          @reset_button.hide()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html(@out_of_sync_message)

  next_problem: =>
    if @child_state == 'done'
      $.postWithPrefix "#{@ajax_url}/next_problem", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @coe.after(response.html).remove()
          @reinitialize(@element)
          @rebind()
          @next_problem_button.hide()
          if !response.allow_reset
            @gentle_alert gettext "Moved to next step."
          else
            ###
            Translators: this message appears when transitioning between openended grading
            types (i.e. self assesment to peer assessment). Sometimes, if a student
            did not perform well at one step, they cannot move on to the next one.
            ###
            @gentle_alert gettext "Your score did not meet the criteria to move to the next step."
            @show_combined_rubric_current()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html(@out_of_sync_message)

  gentle_alert: (msg) =>
    if @$el.find(@oe_alert_sel).length
      @$el.find(@oe_alert_sel).remove()
    alert_elem = "<div class='open-ended-alert' role='alert'>" + msg + "</div>"
    @$el.find('.open-ended-action').after(alert_elem)
    @$el.find(@oe_alert_sel).css(opacity: 0).animate(opacity: 1, 700)

  queueing: =>
    if @child_state=="assessing" and @child_type=="openended"
      if window.queuePollerID # Only one poller 'thread' per Problem
        window.clearTimeout(window.queuePollerID)
      window.queuePollerID = window.setTimeout(@poll, 10000)

  poll: =>
    $.postWithPrefix "#{@ajax_url}/check_for_score", (response) =>
      if response.state == "done" or response.state=="post_assessment"
        delete window.queuePollerID
        @reload()
      else
        window.queuePollerID = window.setTimeout(@poll, 10000)

  setup_file_upload: =>
    if @accept_file_upload == "True"
      if window.File and window.FileReader and window.FileList and window.Blob
        @can_upload_files = true
        @file_upload_area.html('<input type="file" class="file-upload-box"><img class="file-upload-preview" src="#" alt="Uploaded image" />')
        @file_upload_area.show()
        @$(@file_upload_preview_sel).hide()
        @$(@file_upload_box_sel).change @preview_image
      else
        @gentle_alert gettext 'File uploads are required for this question, but are not supported in your browser. Try the newest version of Google Chrome. Alternatively, if you have uploaded the image to another website, you can paste a link to it into the answer box.'

  hide_file_upload: =>
    if @accept_file_upload == "True"
      @file_upload_area.hide()

  replace_text_inputs: =>
    answer_class = @answer_area.attr('class')
    answer_id = @answer_area.attr('id')
    answer_val = @answer_area.val()
    new_text = ''
    new_text = "<div class='#{answer_class}' id='#{answer_id}'>#{answer_val}</div>"
    @answer_area.replaceWith(new_text)

  # wrap this so that it can be mocked
  reload: ->
    @reinitialize()

  collapse_question: (event) =>
    @prompt_container.slideToggle()
    @prompt_container.toggleClass('open')
    if @prompt_container.hasClass('open')
      ###
      Translators: "Show Question" is some text that, when clicked, shows a question's
      content that had been hidden
      ###
      new_text = gettext "Show Question"
      Logger.log 'oe_show_question', {location: @location}
    else
      ###
      Translators: "Hide Question" is some text that, when clicked, hides a question's
      content
      ###
      Logger.log 'oe_hide_question', {location: @location}
      new_text = gettext "Hide Question"
    @question_header.text(new_text)
    return false

  hide_rubrics: () =>
    rubrics = @$(@combined_rubric_sel)
    for rub in rubrics
      if @$(rub).data('status')=="shown"
        @$(rub).show()
      else
        @$(rub).hide()

  next_rubric: =>
    @shift_rubric(1)
    return false

  previous_rubric: =>
    @shift_rubric(-1)
    return false

  shift_rubric: (i) =>
    rubrics = @$(@combined_rubric_sel)
    number = 0
    for rub in rubrics
      if @$(rub).data('status')=="shown"
        number = @$(rub).data('number')
      @$(rub).data('status','hidden')
    if i==1 and number < rubrics.length - 1
      number = number + i

    if i==-1 and number>0
      number = number + i

    @$(rubrics[number]).data('status', 'shown')
    @hide_rubrics()

  prompt_show: () =>
    if @prompt_container.is(":hidden")==true
      @prompt_container.slideToggle()
      @prompt_container.toggleClass('open')
      @question_header.text(gettext "Hide Question")

  prompt_hide: () =>
    if @prompt_container.is(":visible")==true
      @prompt_container.slideToggle()
      @prompt_container.toggleClass('open')
      @question_header.text(gettext "Show Question")

  log_feedback_click: (event) ->
    target = @$(event.target)
    if target.hasClass('see-full-feedback')
      Logger.log 'oe_show_full_feedback', {}
    else if target.hasClass('respond-to-feedback')
      Logger.log 'oe_show_respond_to_feedback', {}
    else
      generated_event_type = link_text.toLowerCase().replace(" ","_")
      Logger.log "oe_" + generated_event_type, {}
  log_feedback_selection: (event) ->
    target_selection = @$(event.target).val()
    Logger.log 'oe_feedback_response_selected', {value: target_selection}

  remove_attribute: (name) =>
    if @$(@file_upload_preview_sel).attr(name)
      @$(@file_upload_preview_sel)[0].removeAttribute(name)

  preview_image: () =>
    if @$(@file_upload_box_sel)[0].files && @$(@file_upload_box_sel)[0].files[0]
      reader = new FileReader()
      reader.onload = (e) =>
        max_dim = 150
        @remove_attribute('src')
        @remove_attribute('height')
        @remove_attribute('width')
        @$(@file_upload_preview_sel).attr('src', e.target.result)
        height_px = @$(@file_upload_preview_sel)[0].height
        width_px = @$(@file_upload_preview_sel)[0].width
        scale_factor = 0
        if height_px>width_px
          scale_factor = height_px/max_dim
        else
          scale_factor = width_px/max_dim
        @$(@file_upload_preview_sel)[0].width = width_px/scale_factor
        @$(@file_upload_preview_sel)[0].height = height_px/scale_factor
        @$(@file_upload_preview_sel).show()
      reader.readAsDataURL(@$(@file_upload_box_sel)[0].files[0])

  toggle_rubric: (event) =>
    info_rubric_elements = @$(@info_rubric_elements_sel)
    info_rubric_elements.slideToggle()
    return false

  setup_score_selection: () =>
    @$("input[class='score-selection']").change @graded_callback

  graded_callback: () =>
    if @rub.check_complete()
      @submit_button.attr("disabled",false)
      @submit_button.show()
