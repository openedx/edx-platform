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
      queuelen = @get_queuelen()
      window.queuePollerID = window.setTimeout(@poll, queuelen*10)

  # Retrieves the minimum queue length of all queued items
  get_queuelen: =>
    minlen = Infinity
    @queued_items.each (index, qitem) ->
      len = parseInt($.text(qitem))  
      if len < minlen
        minlen = len
    return minlen
    
  poll: =>
    $.postWithPrefix "#{@url}/problem_get", (response) =>
      @queued_items = $(response.html).find(".xqueue")
      if @queued_items.length == 0 
        @el.html(response.html)
        @executeProblemScripts () =>
          @setupInputTypes()
          @bind()
        delete window.queuePollerID
      else
        # TODO: Some logic to dynamically adjust polling rate based on queuelen
        window.queuePollerID = window.setTimeout(@poll, 1000)

  render: (content) ->
    if content
      @el.html(content)
      @executeProblemScripts () =>
        @setupInputTypes()
        @bind()
        @queueing()
    else
      $.postWithPrefix "#{@url}/problem_get", (response) =>
        @el.html(response.html)
        @executeProblemScripts () =>
          @setupInputTypes()
          @bind()
          @queueing()

  # TODO add hooks for problem types here by inspecting response.html and doing
  # stuff if a div w a class is found

  setupInputTypes: =>
    @el.find(".capa_inputtype").each (index, inputtype) =>
      classes = $(inputtype).attr('class').split(' ')
      for cls in classes
        setupMethod = @inputtypeSetupMethods[cls]
        setupMethod(inputtype) if setupMethod?

  executeProblemScripts: (callback=null) ->

    placeholders = @el.find(".script_placeholder")

    if placeholders.length == 0
      callback()
      return

    completed      = (false for i in [1..placeholders.length])
    callbackCalled = false

    # This is required for IE8 support.
    completionHandlerGeneratorIE = (index) =>
      return () ->
        if (this.readyState == 'complete' || this.readyState == 'loaded')
          #completionHandlerGenerator.call(self, index)()
          completionHandlerGenerator(index)()

    completionHandlerGenerator = (index) =>
      return () =>
        allComplete = true
        completed[index] = true
        for flag in completed
          if not flag
            allComplete = false
            break
        if allComplete and not callbackCalled
          callbackCalled = true
          callback() if callback?

    placeholders.each (index, placeholder) ->
      s = document.createElement('script')
      s.setAttribute('src', $(placeholder).attr("data-src"))
      s.setAttribute('type', "text/javascript")

      s.onload             = completionHandlerGenerator(index)

      # s.onload does not fire in IE8; this does.
      s.onreadystatechange = completionHandlerGeneratorIE(index)

      # Need to use the DOM elements directly or the scripts won't execute
      # properly.
      $('head')[0].appendChild(s)
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
    
    # Sanity check of file size
    file_too_large = false
    max_filesize = 10*1000*1000 # 10 MB

    @inputs.each (index, element) ->
      if element.type is 'file'
        if element.files[0] instanceof File
          if element.files[0].size > max_filesize
            file_too_large = true
            alert 'Submission aborted! Your file "' + element.files[0].name + '" is too large (max size: ' + max_filesize/(1000*1000) + ' MB)'
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

    if not file_too_large
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

  # TODO this needs modification to deal with javascript responses; perhaps we
  # need something where responsetypes can define their own behavior when show
  # is called.
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

  inputtypeSetupMethods:
    javascriptinput: (element) =>

      data = $(element).find(".javascriptinput_data")

      params        = data.data("params")
      submission    = data.data("submission")
      evaluation    = data.data("evaluation")
      problemState  = data.data("problem_state")
      displayClass  = window[data.data('display_class')]

      container = $(element).find(".javascriptinput_container")
      submissionField = $(element).find(".javascriptinput_input")

      display = new displayClass(problemState, submission, evaluation, container, submissionField, params)
      display.render()
