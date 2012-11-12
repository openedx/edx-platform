class @SelfAssessment
  constructor: (element) ->
    @el = $(element).find('section.self-assessment')
    @id = @el.data('id')
    @ajax_url = @el.data('ajax-url')
    @state = @el.data('state')
    # valid states: 'initial', 'assessing', 'request_hint', 'done'

    # Where to put the rubric once we load it
    @errors_area = @$('.error')
    @answer_area = @$('textarea.answer')

    @rubric_wrapper = @$('.rubric-wrapper')
    @hint_wrapper = @$('.hint-wrapper')
    @message_wrapper = @$('.message-wrapper')
    @check_button = @$('.submit-button')

    @find_assessment_elements()
    @find_hint_elements()

    @bind()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  bind: () =>
    # rebind to the appropriate function for the current state
    @check_button.unbind('click')
    if @state == 'initial'
      @check_button.click @save_answer
    else if @state == 'assessing'
      @check_button.click @save_assessment
    else if @state == 'request_hint'
      @check_button.click @save_hint
    else if @state == 'done'
      @check_button.hide()

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
          @bind()
        else
          @errors_area.html(response.message)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')

  save_assessment: (event) =>
    event.preventDefault()
    if @state == 'assessing'
      data = {'assessment' : @assessment.find(':selected').text()}
      $.postWithPrefix "#{@ajax_url}/save_assessment", data, (response) =>
        if response.success
          @hint_wrapper.html(response.hint_html)
          @state = 'request_hint'
          @find_hint_elements()
          @bind()
        else
          @errors_area.html(response.message)
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
          @bind()
        else
          @errors_area.html(response.message)
    else
      @errors_area.html('Problem state got out of sync.  Try reloading the page.')
      
