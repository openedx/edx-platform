class @Problem
  constructor: (element) ->
    @el = $(element).find('.problems-wrapper')
    @id = @el.data('problem-id')
    @element_id = @el.attr('id')
    @url = @el.data('url')

    # Destroy any existing polling threads on Problem change
    if window.queuePollerID
      window.clearTimeout(window.queuePollerID)
      delete window.queuePollerID

    @render()

  $: (selector) ->
    $(selector, @el)

  bind: =>
    MathJax.Hub.Queue ["Typeset", MathJax.Hub]
    window.update_schematics()

    problem_prefix = @element_id.replace(/problem_/,'')
    @inputs = @$("[id^=input_#{problem_prefix}_]")
    
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

  queueing: =>
    @queued_items = @$(".xqueue")
    if @queued_items.length > 0
      if window.queuePollerID # Only one poller 'thread' per Problem
        window.clearTimeout(window.queuePollerID)
      window.queuePollerID = window.setTimeout(@poll, 100)

  poll: =>
    $.postWithPrefix "#{@url}/problem_get", (response) =>
      @el.html(response.html)
      @executeProblemScripts()
      @bind()

      @queued_items = @$(".xqueue")
      if @queued_items.length == 0 
        delete window.queuePollerID
      else
        # TODO: Dynamically adjust timeout interval based on @queued_items.value
        window.queuePollerID = window.setTimeout(@poll, 1000)

  render: (content) ->
    if content
      @el.html(content)
      @bind()
      @queueing()
    else
      $.postWithPrefix "#{@url}/problem_get", (response) =>
        @el.html(response.html)
        @executeProblemScripts()
        @bind()
        @queueing()

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

    # If there are no file inputs in the problem, we can fall back on @check
    if $('input:file').length == 0 
      @check()
      return

    if not window.FormData
      alert "Sorry, your browser does not support file uploads. Your submit request could not be fulfilled. If you can, please use Chrome or Safari which have been verified to support file uploads."
      return

    fd = new FormData()
    
    @inputs.each (index, element) ->
      if element.type is 'file'
        if element.files[0] instanceof File
          fd.append(element.id, element.files[0])
        else
          fd.append(element.id, '')
      else
        fd.append(element.id, element.value)

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
    @answers = @inputs.serialize()
