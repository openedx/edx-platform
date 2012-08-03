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
    MathJax.Hub.Queue ["Typeset", MathJax.Hub]
    window.update_schematics()
    @$('section.action input:button').click @refreshAnswers
    @$('section.action input.check').click @check_fd
    #@$('section.action input.check').click @check
    @$('section.action input.reset').click @reset
    @$('section.action input.show').click @show
    @$('section.action input.save').click @save
    @$('input.math').keyup(@refreshMath).each(@refreshMath)

  updateProgress: (response) =>
    if response.progress_changed
        @el.attr progress: response.progress_status
        @el.trigger('progressChanged')

  render: (content) ->
    if content
      @el.html(content)
      @bind()
    else
      $.postWithPrefix "#{@url}/problem_get", (response) =>
        @el.html(response.html)
        @executeProblemScripts()
        @bind()

  executeProblemScripts: ->
    @el.find(".script_placeholder").each (index, placeholder) ->
      s = $("<script>")
      s.attr("type", "text/javascript")
      s.attr("src", $(placeholder).attr("data-src"))

      # Need to use the DOM elements directly or the scripts won't execute
      # properly.
      $('head')[0].appendChild(s[0])
      $(placeholder).remove()

  ###
  # 'check_fd' uses FormData to allow file submissions in the 'problem_check' dispatch,
  #      in addition to simple querystring-based answers
  #
  # NOTE: The dispatch 'problem_check' is being singled out for the use of FormData;
  #       maybe preferable to consolidate all dispatches to use FormData
  ###
  check_fd: =>
    Logger.log 'problem_check', @answers

    if not window.FormData
      alert "Sorry, your browser does not support file uploads. If you can, please use Chrome or Safari which have been verified to support this feature."
      return

    fd = new FormData()

    # For each file input, allow a single file submission,
    #   which is routed to Django 'request.FILES'
    @$('input:file').each (index, element) ->
      if element.files[0] instanceof File
        fd.append(element.id, element.files[0])
      else
        fd.append(element.id, '')  # Even if no file selected, need to include input id

    # Simple (non-file) answers, which is routed to Django 'request.POST'
    fd.append('__answers_querystring', @answers)

    settings = 
      type: "POST"
      data: fd
      processData: false
      contentType: false
      success: (response) => 
        switch response.success
          when 'incorrect', 'correct'
            @render(response.contents)
            @updateProgress response
          else
            alert(response.success)

    $.ajaxWithPrefix("#{@url}/problem_check", settings)

  check: =>
    Logger.log 'problem_check', @answers
    $.postWithPrefix "#{@url}/problem_check", @answers, (response) =>
      switch response.success
        when 'incorrect', 'correct'
          @render(response.contents)
          @updateProgress response
        else
          alert(response.success)

  reset: =>
    Logger.log 'problem_reset', @answers
    $.postWithPrefix "#{@url}/problem_reset", id: @id, (response) =>
        @render(response.html)
        @updateProgress response

  show: =>
    if !@el.hasClass 'showed'
      Logger.log 'problem_show', problem: @id
      $.postWithPrefix "#{@url}/problem_show", (response) =>
        answers = response.answers
        $.each answers, (key, value) =>
          if $.isArray(value)
            for choice in value
              @$("label[for='input_#{key}_#{choice}']").attr correct_answer: 'true'
          else
            @$("#answer_#{key}, #solution_#{key}").html(value)
        MathJax.Hub.Queue ["Typeset", MathJax.Hub]
        @$('.show').val 'Hide Answer'
        @el.addClass 'showed'
        @updateProgress response
    else
      @$('[id^=answer_], [id^=solution_]').text ''
      @$('[correct_answer]').attr correct_answer: null
      @el.removeClass 'showed'
      @$('.show').val 'Show Answer'

  save: =>
    Logger.log 'problem_save', @answers
    $.postWithPrefix "#{@url}/problem_save", @answers, (response) =>
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
    @answers = @$("[id^=input_#{@element_id.replace(/problem_/, '')}_]").serialize()
