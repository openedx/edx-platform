class @CombinedOpenEnded
  constructor: (element) ->
    @el = $(element).find('section.combined-open-ended')
    @id = @el.data('id')
    @ajax_url = @el.data('ajax-url')
    @state = @el.data('state')
    @allow_reset = @el.data('allow_reset')
    @reset_button = @$('.reset-button')
    @reset_button.click @reset
    @next_problem_button = @$('.next-step-button')
    @next_problem_button.click @next_problem
    @combined_open_ended= @$('.combined-open-ended')
    # valid states: 'initial', 'assessing', 'post_assessment', 'done'

    # Where to put the rubric once we load it
    @el = $(element).find('section.open-ended-child')
    @errors_area = @$('.error')
    @answer_area = @$('textarea.answer')

    @rubric_wrapper = @$('.rubric-wrapper')
    @hint_wrapper = @$('.hint-wrapper')
    @message_wrapper = @$('.message-wrapper')
    @submit_button = @$('.submit-button')
    @child_state = @el.data('state')

    @open_ended_child= @$('.open-ended-child')

    @find_assessment_elements()
    @find_hint_elements()

    @rebind()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  rebind: () =>
    # rebind to the appropriate function for the current state
    @submit_button.unbind('click')
    @submit_button.show()
    @reset_button.hide()
    @next_problem_button.hide()
    @hint_area.attr('disabled', false)
    if @child_state == 'initial'
      @answer_area.attr("disabled", false)
      @submit_button.prop('value', 'Submit')
      @submit_button.click @save_answer
    else if @child_state == 'assessing'
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit assessment')
      @submit_button.click @save_assessment
    else if @child_state == 'post_assessment'
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit hint')
      @submit_button.click @save_hint
    else if @child_state == 'done'
      @answer_area.attr("disabled", true)
      @hint_area.attr('disabled', true)
      @submit_button.hide()
      if !@state == 'done'
        @next_problem_button.show()
        if @allow_reset
          @reset_button.show()
        else
          @reset_button.hide()

  find_assessment_elements: ->
    @assessment = @$('select.assessment')

  find_hint_elements: ->
    @hint_area = @$('textarea.hint')

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

      $.postWithPrefix "#{@ajax_url}/save_hint", data, (response) =>
        if response.success
          @message_wrapper.html(response.message_html)
          @child_state = 'done'
          @allow_reset = response.allow_reset
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')


  reset: (event) =>
    event.preventDefault()
    @errors_area.html('Problem state got out of sync.  Try reloading the page.')
    if @child_state == 'done'
      $.postWithPrefix "#{@ajax_url}/reset", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @rebind()
          @reset_button.hide()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  next_problem (event) =>
    event.preventDefault()
    @errors_area.html('Problem state got out of sync.  Try reloading the page.')
    if @child_state == 'done'
      $.postWithPrefix "#{@ajax_url}/next_problem", {}, (response) =>
        if response.success
          @answer_area.val('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @child_state = 'initial'
          @rebind()
          @reset_button.hide()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')