class @Problem
  constructor: (@id, url) ->
    @element = $("#problem_#{id}")
    @render()

  $: (selector) ->
    $(selector, @element)

  bind: =>
    MathJax.Hub.Queue ["Typeset", MathJax.Hub]
    window.update_schematics()
    @$('section.action input:button').click @refreshAnswers
    @$('section.action input.check').click @check
    @$('section.action input.reset').click @reset
    @$('section.action input.show').click @show
    @$('section.action input.save').click @save
    @$('input.math').keyup(@refreshMath).each(@refreshMath)

  updateProgress: (response) =>
    if response.progress_changed
        @element.attr progress: response.progress_status
        @element.trigger('progressChanged')

  render: (content) ->
    if content
      @element.html(content)
      @bind()
    else
      $.postWithPrefix "/modx/problem/#{@id}/problem_get", (response) =>
        @element.html(response.html)
        @bind()

  check: =>
    Logger.log 'problem_check', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_check", @answers, (response) =>
      switch response.success
        when 'incorrect', 'correct'
          @render(response.contents)
          @updateProgress response
        else
          alert(response.success)

  reset: =>
    Logger.log 'problem_reset', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_reset", id: @id, (response) =>
        @render(response.html)
        @updateProgress response

  show: =>
    if !@element.hasClass 'showed'
      Logger.log 'problem_show', problem: @id
      $.postWithPrefix "/modx/problem/#{@id}/problem_show", (response) =>
        answers = response.answers
        $.each answers, (key, value) =>
          if $.isArray(value)
            for choice in value
              @$("label[for='input_#{key}_#{choice}']").attr correct_answer: 'true'
          else
            @$("#answer_#{key}, #solution_#{key}").html(value)
        MathJax.Hub.Queue ["Typeset", MathJax.Hub]
        @$('.show').val 'Hide Answer'
        @element.addClass 'showed'
        @updateProgress response
    else
      @$('[id^=answer_], [id^=solution_]').text ''
      @$('[correct_answer]').attr correct_answer: null
      @element.removeClass 'showed'
      @$('.show').val 'Show Answer'

  save: =>
    Logger.log 'problem_save', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_save", @answers, (response) =>
      if response.success
        alert 'Saved'
      @updateProgress response

  refreshMath: (event, element) =>
    element = event.target unless element
    target = "display_#{element.id.replace(/^input_/, '')}"

    if jax = MathJax.Hub.getAllJax(target)[0]
      MathJax.Hub.Queue ['Text', jax, $(element).val()],
        [@updateMathML, jax, element]

  updateMathML: (jax, element) =>
    try
      $("##{element.id}_dynamath").val(jax.root.toMathML '')
    catch exception
      throw exception unless exception.restart
      MathJax.Callback.After [@refreshMath, jax], exception.restart

  refreshAnswers: =>
    @$('input.schematic').each (index, element) ->
      element.schematic.update_value()
    @$(".CodeMirror").each (index, element) ->
      element.CodeMirror.save() if element.CodeMirror.save
    @answers = @$("[id^=input_#{@id}_]").serialize()
