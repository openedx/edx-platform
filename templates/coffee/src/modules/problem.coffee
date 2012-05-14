class @Problem
  constructor: (@id, url) ->
    @element = $("#problem_#{id}")
    @content_url = "#{url}problem_get?id=#{@id}"
    @render()

  $: (selector) ->
    $(selector, @element)

  bind: =>
    MathJax.Hub.Queue ["Typeset",MathJax.Hub]
    window.update_schematics()
    @$('section.action input:button').click @refreshAnswers
    @$('section.action input.check').click @check
    @$('section.action input.reset').click @reset
    @$('section.action input.show').click @show
    @$('section.action input.save').click @save

  render: (content) ->
    if content
      @element.html(content)
      @bind()
    else
      @element.load @content_url, @bind

  check: =>
    Logger.log 'problem_check', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_check", @answers, (response) =>
      switch response.success
        when 'incorrect', 'correct'
          @render(response.contents)
        else
          alert(response.success)

  reset: =>
    Logger.log 'problem_reset', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_reset", id: @id, (content) =>
      @render(content)

  show: =>
    Logger.log 'problem_show', problem: @id
    $.postWithPrefix "/modx/problem/#{@id}/problem_show", (response) =>
      $.each response, (key, value) =>
        @$("#answer_#{key}").text(value)

  save: =>
    Logger.log 'problem_save', @answers
    $.postWithPrefix "/modx/problem/#{@id}/problem_save", @answers, (response) =>
      if response.success
        alert 'Saved'

  refreshAnswers: =>
    @answers = {}
    @$('input.schematic').each (index, element) ->
      element.schematic.update_value()
    $.each @$("[id^=input_#{@id}_]"), (index, input) =>
      @answers[$(input).attr('id')] = $(input).val()
