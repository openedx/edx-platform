class @SelfAssessment
  constructor: (element) ->
    @el = $(element).find('section.self-assessment')
    @id = @el.data('id')
    @ajax_url = @el.data('ajax-url')
    @state = @el.data('state')
    @allow_reset = @el.data('allow_reset')
    # valid states: 'initial', 'assessing', 'request_hint', 'done'

    # Where to put the rubric once we load it
    @errors_area = @$('.error')
    @answer_area = @$('textarea.answer')

    @rubric_wrapper = @$('.rubric-wrapper')
    @hint_wrapper = @$('.hint-wrapper')
    @message_wrapper = @$('.message-wrapper')
    @submit_button = @$('.submit-button')
    @reset_button = @$('.reset-button')
    @reset_button.click @reset

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
    @hint_area.attr('disabled', false)
    if @state == 'initial'
      @answer_area.attr("disabled", false)
      @submit_button.prop('value', 'Submit')
      @submit_button.click @save_answer
    else if @state == 'assessing'
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit assessment')
      @submit_button.click @save_assessment
    else if @state == 'request_hint'
      @answer_area.attr("disabled", true)
      @submit_button.prop('value', 'Submit hint')
      @submit_button.click @save_hint
    else if @state == 'done'
      @answer_area.attr("disabled", true)
      @hint_area.attr('disabled', true)
      @submit_button.hide()
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
    if @state == 'initial'
      data = {'student_answer' : @answer_area.val()}
      $.postWithPrefix "#{@ajax_url}/save_answer", data, (response) =>
        if response.success
          @rubric_wrapper.html(response.rubric_html)
          @state = 'assessing'
          @find_assessment_elements()
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  save_assessment: (event) =>
    event.preventDefault()
    if @state == 'assessing'
      data = {'assessment' : @assessment.find(':selected').text()}
      $.postWithPrefix "#{@ajax_url}/save_assessment", data, (response) =>
        if response.success
          @state = response.state

          if @state == 'request_hint'
            @hint_wrapper.html(response.hint_html)
            @find_hint_elements()
          else if @state == 'done'
            @message_wrapper.html(response.message_html)
            @allow_reset = response.allow_reset

          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')
    

  save_hint:  (event) =>
    event.preventDefault()
    if @state == 'request_hint'
      data = {'hint' : @hint_area.val()}
      
      $.postWithPrefix "#{@ajax_url}/save_hint", data, (response) =>
        if response.success
          @message_wrapper.html(response.message_html)
          @state = 'done'
          @allow_reset = response.allow_reset
          @rebind()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')
      

  reset: (event) =>
    event.preventDefault()
    if @state == 'done'
      $.postWithPrefix "#{@ajax_url}/reset", {}, (response) =>
        if response.success
          @answer_area.html('')
          @rubric_wrapper.html('')
          @hint_wrapper.html('')
          @message_wrapper.html('')
          @state = 'initial'
          @rebind()
          @reset_button.hide()
        else
          @errors_area.html(response.error)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')
