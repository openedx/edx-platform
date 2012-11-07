class @SelfAssessment
  constructor: (element) ->
    @el = $(element).find('section.self-assessment')
    @id = @el.data('id')
    @ajax_url = @el.data('ajax-url')

    # Where to put the rubric once we load it
    @rubric_wrapper = @$('.rubric-wrapper')
    @check_button = @$('.submit-button')
    @answer_area = @$('textarea.answer')
    @errors_area = @$('.error')
    @state = 'prompt'    # switches to 'eval' after answer is submitted
    @bind()

  # locally scoped jquery.
  $: (selector) ->
    $(selector, @el)

  bind: ->
    @check_button.click @show_rubric

  find_eval_elements: ->
    # find the elements we'll need from the newly loaded rubric data
    @assessment = @$('select.assessment')
    @hint = @$('textarea.hint')
    @save_message = @$('.save_message')

  show_rubric: (event) =>
    event.preventDefault()
    if @state == 'prompt'
      data = {'student_answer' : @answer_area.val()}
      $.postWithPrefix "#{@ajax_url}/show", data, (response) =>
        if response.success
          @rubric_wrapper.html(response.rubric)
          @state = 'eval'
          @find_eval_elements()
        else
          @errors_area.html(response.message)
    else
      data = {'assessment' : @assessment.find(':selected').text(), 'hint' : @hint.val()}
              
      $.postWithPrefix "#{@ajax_url}/save", data, (response) =>
        if response.success
          @rubric_wrapper.html(response.message)
        else
          @errors_area.html('There was an error saving your response.')
