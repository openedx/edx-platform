class @Problem

  constructor: (element) ->
    @el = $(element).find('.problems-wrapper')
    @id = @el.data('problem-id')
    @element_id = @el.attr('id')
    @url = @el.data('url')
    @render()

  $: (selector) ->
    $(selector, @el)

  bind: =>
    problem_prefix = @element_id.replace(/sa_/,'')
    @inputs = @$("[id^=input_#{problem_prefix}_]")

    @$('section.action input.show').click @show
    @$('section.action input.save').click @save

  render: (content) ->
    if content
      @el.html(content)
      JavascriptLoader.executeModuleScripts @el, () =>
        @setupInputTypes()
        @bind()
    else
      $.postWithPrefix "#{@url}/sa_get", (response) =>
        @el.html(response.html)
        JavascriptLoader.executeModuleScripts @el, () =>
          @setupInputTypes()
          @bind()


  # TODO add hooks for problem types here by inspecting response.html and doing
  # stuff if a div w a class is found

  show: =>
    Logger.log 'sa_show', problem: @id
    $.postWithPrefix "#{@url}/sa_show", (response) =>
      answers = response.answers
      $.each answers, (key, value) =>
        if $.isArray(value)
          for choice in value
            @$("label[for='input_#{key}_#{choice}']").attr correct_answer: 'true'
        else
          answer = @$("#answer_#{key}, #solution_#{key}")
          answer.html(value)
          Collapsible.setCollapsibles(answer)

      @$('.show').val 'Hide Answer'
      @el.addClass 'showed'

  save: =>
    Logger.log 'problem_save', @answers
    $.postWithPrefix "#{@url}/problem_save", @answers, (response) =>
      if response.success
        saveMessage = "Your answers have been saved but not graded. Hit 'Check' to grade them."
        @gentle_alert saveMessage
      @updateProgress response

  inputtypeShowAnswerMethods:
    choicegroup: (element, display, answers) =>
      element = $(element)

      element.find('input').attr('disabled', 'disabled')

      input_id = element.attr('id').replace(/inputtype_/,'')
      answer = answers[input_id]
      for choice in answer
        element.find("label[for='input_#{input_id}_#{choice}']").addClass 'choicegroup_correct'

    javascriptinput: (element, display, answers) =>
      answer_id = $(element).attr('id').split("_")[1...].join("_")
      answer = JSON.parse(answers[answer_id])
      display.showAnswer(answer)

  inputtypeHideAnswerMethods:
    choicegroup: (element, display) =>
      element = $(element)
      element.find('input').attr('disabled', null)
      element.find('label').removeClass('choicegroup_correct')

    javascriptinput: (element, display) =>
      display.hideAnswer()
