class @SelfAssessment

  constructor: (element) ->
    @el = $(element).find('.sa-wrapper')
    @id = @el.data('sa-id')
    @element_id = @el.attr('id')
    @url = @el.data('url')
    @render()

  $: (selector) ->
    $(selector, @el)

  bind: =>

    window.update_schematics()

    problem_prefix = @element_id.replace(/sa_/,'')
    @inputs = @$("[id^=input_#{problem_prefix}_]")

    @$('input:button').click @refreshAnswers
    #@$('section.action input.check').click @check
    @$('input.show').click @show
    @$('input.save').click @save

    # Collapsibles
    Collapsible.setCollapsibles(@el)

    # Dynamath
    @$('input.math').keyup(@refreshMath)
    @$('input.math').each (index, element) =>
      MathJax.Hub.Queue [@refreshMath, null, element]

  updateProgress: (response) =>
    if response.progress_changed
      @el.attr progress: response.progress_status
      @el.trigger('progressChanged')

  show: =>
    $.postWithPrefix "#{@url}/sa_show", (response) =>
      answers = response.answers
      @el.addClass 'showed'

  save: =>
    $.postWithPrefix "/sa_save", @answers, (response) =>
      if response.success
       @$('p.rubric').replace(response.rubric)

  render: (content) ->
    if content
      @el.html(content)
      JavascriptLoader.executeModuleScripts @el, () =>
        @setupInputTypes()
        @bind()
    else
      $.postWithPrefix "#{@url}/problem_get", (response) =>
        @el.html(response.html)
        JavascriptLoader.executeModuleScripts @el, () =>
          @setupInputTypes()
          @bind()

  setupInputTypes: =>
    @inputtypeDisplays = {}
    @el.find(".capa_inputtype").each (index, inputtype) =>
      classes = $(inputtype).attr('class').split(' ')
      id = $(inputtype).attr('id')
      for cls in classes
        setupMethod = @inputtypeSetupMethods[cls]
        if setupMethod?
          @inputtypeDisplays[id] = setupMethod(inputtype)

  gentle_alert: (msg) =>
    if @el.find('.capa_alert').length
      @el.find('.capa_alert').remove()
    alert_elem = "<div class='capa_alert'>" + msg + "</div>"
    @el.find('.action').after(alert_elem)
    @el.find('.capa_alert').css(opacity: 0).animate(opacity: 1, 700)

  refreshAnswers: =>
    @$('input.schematic').each (index, element) ->
      element.schematic.update_value()
    @$(".CodeMirror").each (index, element) ->
      element.CodeMirror.save() if element.CodeMirror.save
    @answers = @inputs.serialize()

  inputtypeSetupMethods:

    'text-input-dynamath': (element) =>
      ###
      Return: function (eqn) -> eqn that preprocesses the user formula input before
                it is fed into MathJax. Return 'false' if no preprocessor specified
      ###
      data = $(element).find('.text-input-dynamath_data')

      preprocessorClassName = data.data('preprocessor')
      preprocessorClass = window[preprocessorClassName]
      if not preprocessorClass?
        return false
      else
        preprocessor = new preprocessorClass()
        return preprocessor.fn

    javascriptinput: (element) =>

      data = $(element).find(".javascriptinput_data")

      params        = data.data("params")
      submission    = data.data("submission")
      evaluation    = data.data("evaluation")
      problemState  = data.data("problem_state")
      displayClass  = window[data.data('display_class')]

      if evaluation == ''
        evaluation = null

      container = $(element).find(".javascriptinput_container")
      submissionField = $(element).find(".javascriptinput_input")

      display = new displayClass(problemState, submission, evaluation, container, submissionField, params)
      display.render()

      return display

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


