class @CombinedOpenEnded
  constructor: (element) ->
    @element=element
    @reinitialize(element)

  reinitialize: (element) ->
    @wrapper=$(element).find('section.xmodule_CombinedOpenEndedModule')
    @el = $(element).find('section.combined-open-ended')
    @combined_open_ended=$(element).find('section.combined-open-ended')
    @id = @el.data('id')
    @ajax_url = @el.data('ajax-url')
    @state = @el.data('state')
    @task_count = @el.data('task-count')
    @task_number = @el.data('task-number')

    @allow_reset = @el.data('allow_reset')
    @reset_button = @$('.reset-button')
    @reset_button.click @reset
    @next_problem_button = @$('.next-step-button')
    @next_problem_button.click @next_problem

    @show_results_button=@$('.show-results-button')
    @show_results_button.click @show_results

    # valid states: 'initial', 'assessing', 'post_assessment', 'done'
    Collapsible.setCollapsibles(@el)
    @submit_evaluation_button = $('.submit-evaluation-button')
    @submit_evaluation_button.click @message_post

    @results_container = $('.result-container')

    # Where to put the rubric once we load it
    @el = $(element).find('section.open-ended-child')
    @errors_area = @$('.error')
    @answer_area = @$('textarea.answer')

    @rubric_wrapper = @$('.rubric-wrapper')
    @hint_wrapper = @$('.hint-wrapper')
    @message_wrapper = @$('.message-wrapper')
    @submit_button = @$('.submit-button')
    @child_state = @el.data('state')
    @child_type = @el.data('child-type')
    if @child_type=="openended"
      @skip_button = @$('.skip-button')
      @skip_button.click @skip_post_assessment

    @open_ended_child= @$('.open-ended-child')

    @find_assessment_elements()
    @find_hint_elements()

    @rebind()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  show_results: (event) =>
    status_item = $(event.target).parent().parent()
    status_number = status_item.data('status-number')
    data = {'task_number' : status_number}
    $.postWithPrefix "#{@ajax_url}/get_results", data, (response) =>
      if response.success
        @results_container.after(response.html).remove()
        @Collapsible.setCollapsibles(@results_container)
      else
        @errors_area.html(response.error)

  rebind: () =>
    # rebind to the appropriate function for the current state
    @submit_button.unbind('click')
    @submit_button.show()
    @reset_button.hide()
    @next_problem_button.hide()
    @hint_area.attr('disabled', false)
    if @child_type=="openended"
      @skip_button.hide()
    if @child_state == 'initial'
      @answer_area.attr("disabled", false)
      @submit_button.prop('value', 'Submit')
      @submit_button.click @save_answer
    else if @child_state == 'assessing'
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit assessment')
      @submit_button.click @save_assessment
      if @child_type == "openended"
        @submit_button.hide()
        @queueing()
    else if @child_state == 'post_assessment'
      if @child_type=="openended"
        @skip_button.show()
        @skip_post_assessment()
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit post-assessment')
      if @child_type=="selfassessment"
         @submit_button.click @save_hint
      else
        @submit_button.click @message_post
    else if @child_state == 'done'
      @answer_area.attr("disabled", true)
      @hint_area.attr('disabled', true)
      @submit_button.hide()
      if @child_type=="openended"
        @skip_button.hide()
      if @task_number<@task_count
        @next_problem()
      else
        @reset_button.show()


  find_assessment_elements: ->
    @assessment = @$('select.assessment')

  find_hint_elements: ->
    @hint_area = @$('textarea.post_assessment')

  save_answer: (event) =>
    event.preventDefault()
    if @child_state == 'initial'
      data = {'student_answer' : @answer_area.val()}
      $.postWithPrefix "#{@ajax_url}/save_answer", data, (response) =>
        if response.success
          @rubric_wrapper.html(response.rubric_html)
          @child_state = 'assessing'
          @find_assessment_elements()
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  save_assessment: (event) =>
    event.preventDefault()
    if @child_state == 'assessing'
      data = {'assessment' : @assessment.find(':selected').text()}
      $.postWithPrefix "#{@ajax_url}/save_assessment", data, (response) =>
        if response.success
          @child_state = response.state

          if @child_state == 'post_assessment'
            @hint_wrapper.html(response.hint_html)
            @find_hint_elements()
          else if @child_state == 'done'
            @message_wrapper.html(response.message_html)
            @allow_reset = response.allow_reset

          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  save_hint:  (event) =>
    event.preventDefault()
    if @child_state == 'post_assessment'
      data = {'hint' : @hint_area.val()}

      $.postWithPrefix "#{@ajax_url}/save_post_assessment", data, (response) =>
        if response.success
          @message_wrapper.html(response.message_html)
          @child_state = 'done'
          @allow_reset = response.allow_reset
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  skip_post_assessment: =>
    if @child_state == 'post_assessment'

      $.postWithPrefix "#{@ajax_url}/skip_post_assessment", {}, (response) =>
        if response.success
          @child_state = 'done'
          @allow_reset = response.allow_reset
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  reset: (event) =>
    event.preventDefault()
    if @child_state == 'done'
      $.postWithPrefix "#{@ajax_url}/reset", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @combined_open_ended.after(response.html).remove()
          @reinitialize(@element)
          @rebind()
          @reset_button.hide()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  next_problem: =>
    if @child_state == 'done'
      $.postWithPrefix "#{@ajax_url}/next_problem", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @combined_open_ended.after(response.html).remove()
          @reinitialize(@element)
          @rebind()
          @next_problem_button.hide()
          @gentle_alert "Moved to next step."
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  message_post: =>
    Logger.log 'message_post', @answers

    fd = new FormData()
    feedback = $('section.evaluation textarea.feedback-on-feedback')[0].value
    submission_id = $('div.external-grader-message div.submission_id')[0].innerHTML
    grader_id = $('div.external-grader-message div.grader_id')[0].innerHTML
    score = $(".evaluation-scoring input:radio[name='evaluation-score']:checked").val()
    fd.append('feedback', feedback)
    fd.append('submission_id', submission_id)
    fd.append('grader_id', grader_id)
    if(!score)
      @gentle_alert "You need to pick a rating before you can submit."
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
        $('section.evaluation').slideToggle()
        @message_wrapper.html(response.message_html)

    $.ajaxWithPrefix("#{@ajax_url}/save_post_assessment", settings)

  gentle_alert: (msg) =>
    if @el.find('.open-ended-alert').length
      @el.find('.open-ended-alert').remove()
    alert_elem = "<div class='open-ended-alert'>" + msg + "</div>"
    @el.find('.open-ended-action').after(alert_elem)
    @el.find('.open-ended-alert').css(opacity: 0).animate(opacity: 1, 700)

  queueing: =>
    if @child_state=="assessing" and @child_type=="openended"
      if window.queuePollerID # Only one poller 'thread' per Problem
        window.clearTimeout(window.queuePollerID)
      window.queuePollerID = window.setTimeout(@poll, 10000)

  poll: =>
    $.postWithPrefix "#{@ajax_url}/check_for_score", (response) =>
      if response.state == "done" or response.state=="post_assessment"
        delete window.queuePollerID
        location.reload()
      else
        window.queuePollerID = window.setTimeout(@poll, 10000)