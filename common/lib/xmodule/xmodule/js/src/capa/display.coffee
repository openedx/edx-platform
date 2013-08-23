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
    if MathJax?
      @el.find('.problem > div').each (index, element) =>
        MathJax.Hub.Queue ["Typeset", MathJax.Hub, element]

    window.update_schematics()

    problem_prefix = @element_id.replace(/problem_/,'')
    @inputs = @$("[id^=input_#{problem_prefix}_]")
    @$('section.action input:button').click @refreshAnswers
    @$('section.action input.check').click @check_fd
    @$('section.action input.reset').click @reset
    @$('section.action button.show').click @show
    @$('section.action input.save').click @save

    @bindResetCorrectness()

    # Collapsibles
    Collapsible.setCollapsibles(@el)

    # Dynamath
    @$('input.math').keyup(@refreshMath)
    if MathJax?
      @$('input.math').each (index, element) =>
        MathJax.Hub.Queue [@refreshMath, null, element]

  renderProgressState: =>
    detail = @el.data('progress_detail')
    status = @el.data('progress_status')
    # i18n
    progress = "(#{detail} points)"
    if status == 'none' and detail? and detail.indexOf('/') > 0
        a = detail.split('/')
        possible = parseFloat(a[1])
        if possible == 1
            # i18n
            progress = "(#{possible} point possible)"
        else
            # i18n
            progress = "(#{possible} points possible)"
    @$('.problem-progress').html(progress)

  updateProgress: (response) =>
    if response.progress_changed
        @el.data('progress_status', response.progress_status)
        @el.data('progress_detail', response.progress_detail)
        @el.trigger('progressChanged')
    @renderProgressState()

  forceUpdate: (response) =>
    @el.data('progress_status', response.progress_status)
    @el.data('progress_detail', response.progress_detail)
    @el.trigger('progressChanged')
    @renderProgressState()

  queueing: =>
    @queued_items = @$(".xqueue")
    @num_queued_items = @queued_items.length
    if @num_queued_items > 0
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
      # If queueing status changed, then render
      @new_queued_items = $(response.html).find(".xqueue")
      if @new_queued_items.length isnt @num_queued_items
        @el.html(response.html)
        JavascriptLoader.executeModuleScripts @el, () =>
          @setupInputTypes()
          @bind()

      @num_queued_items = @new_queued_items.length
      if @num_queued_items == 0
        @forceUpdate response
        delete window.queuePollerID
      else
        # TODO: Some logic to dynamically adjust polling rate based on queuelen
        window.queuePollerID = window.setTimeout(@poll, 1000)


  # Use this if you want to make an ajax call on the input type object
  # static method so you don't have to instantiate a Problem in order to use it
  # Input:
  #   url: the AJAX url of the problem
  #   input_id: the input_id of the input you would like to make the call on
  #     NOTE: the id is the ${id} part of "input_${id}" during rendering
  #           If this function is passed the entire prefixed id, the backend may have trouble
  #           finding the correct input
  #   dispatch: string that indicates how this data should be handled by the inputtype
  #   callback: the function that will be called once the AJAX call has been completed.
  #             It will be passed a response object
  @inputAjax: (url, input_id, dispatch, data, callback) ->
    data['dispatch'] = dispatch
    data['input_id'] = input_id
    $.postWithPrefix "#{url}/input_ajax", data, callback


  render: (content) ->
    if content
      @el.html(content)
      JavascriptLoader.executeModuleScripts @el, () =>
        @setupInputTypes()
        @bind()
        @queueing()
    else
      $.postWithPrefix "#{@url}/problem_get", (response) =>
        @el.html(response.html)
        JavascriptLoader.executeModuleScripts @el, () =>
          @setupInputTypes()
          @bind()
          @queueing()
          @forceUpdate response

  # TODO add hooks for problem types here by inspecting response.html and doing
  # stuff if a div w a class is found

  setupInputTypes: =>
    @inputtypeDisplays = {}
    @el.find(".capa_inputtype").each (index, inputtype) =>
      classes = $(inputtype).attr('class').split(' ')
      id = $(inputtype).attr('id')
      for cls in classes
        setupMethod = @inputtypeSetupMethods[cls]
        if setupMethod?
          @inputtypeDisplays[id] = setupMethod(inputtype)

  # If some function wants to be called before sending the answer to the
  # server, give it a chance to do so.
  #
  # check_waitfor allows the callee to send alerts if the user's input is
  # invalid. To do so, the callee must throw an exception named "Waitfor
  # Exception". This and any other errors or exceptions that arise from the
  # callee are rethrown and abort the submission.
  #
  # In order to use this feature, add a 'data-waitfor' attribute to the input,
  # and specify the function to be called by the check button before sending
  # off @answers
  check_waitfor: =>
    for inp in @inputs
      if ($(inp).is("input[waitfor]"))
        try
          $(inp).data("waitfor")()
          @refreshAnswers()
        catch e
          if e.name == "Waitfor Exception"
            alert e.message
          else
            alert "Could not grade your answer. The submission was aborted."
          throw e


  ###
  # 'check_fd' uses FormData to allow file submissions in the 'problem_check' dispatch,
  #      in addition to simple querystring-based answers
  #
  # NOTE: The dispatch 'problem_check' is being singled out for the use of FormData;
  #       maybe preferable to consolidate all dispatches to use FormData
  ###
  check_fd: =>
    # If there are no file inputs in the problem, we can fall back on @check
    if $('input:file').length == 0
      @check()
      return

    if not window.FormData
      alert "Submission aborted! Sorry, your browser does not support file uploads. If you can, please use Chrome or Safari which have been verified to support file uploads."
      return

    fd = new FormData()

    # Sanity checks on submission
    max_filesize = 4*1000*1000 # 4 MB
    file_too_large = false
    file_not_selected = false
    required_files_not_submitted = false
    unallowed_file_submitted = false

    errors = []

    @inputs.each (index, element) ->
      if element.type is 'file'
        required_files = $(element).data("required_files")
        allowed_files  = $(element).data("allowed_files")
        for file in element.files
          if allowed_files.length != 0 and file.name not in allowed_files
            unallowed_file_submitted = true
            errors.push "You submitted #{file.name}; only #{allowed_files} are allowed."
          if file.name in required_files
            required_files.splice(required_files.indexOf(file.name), 1)
          if file.size > max_filesize
            file_too_large = true
            errors.push 'Your file "' + file.name '" is too large (max size: ' + max_filesize/(1000*1000) + ' MB)'
          fd.append(element.id, file)
        if element.files.length == 0
          file_not_selected = true
          fd.append(element.id, '') # In case we want to allow submissions with no file
        if required_files.length != 0
          required_files_not_submitted = true
          errors.push "You did not submit the required files: #{required_files}."
      else
        fd.append(element.id, element.value)


    if file_not_selected
      errors.push 'You did not select any files to submit'

    error_html = '<ul>\n'
    for error in errors
      error_html += '<li>' + error + '</li>\n'
    error_html += '</ul>'
    @gentle_alert error_html

    abort_submission = file_too_large or file_not_selected or unallowed_file_submitted or required_files_not_submitted

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
            @gentle_alert response.success
        Logger.log 'problem_graded', [@answers, response.contents], @url

    if not abort_submission
      $.ajaxWithPrefix("#{@url}/problem_check", settings)

  check: =>
    @check_waitfor()
    Logger.log 'problem_check', @answers

    # Segment.io
    analytics.track "Problem Checked",
      problem_id: @id
      answers: @answers

    $.postWithPrefix "#{@url}/problem_check", @answers, (response) =>
      switch response.success
        when 'incorrect', 'correct'
          @render(response.contents)
          @updateProgress response
          if @el.hasClass 'showed'
            @el.removeClass 'showed'
        else
          @gentle_alert response.success
      Logger.log 'problem_graded', [@answers, response.contents], @url

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
            answer = @$("#answer_#{key}, #solution_#{key}")
            answer.html(value)
            Collapsible.setCollapsibles(answer)

        # TODO remove the above once everything is extracted into its own
        # inputtype functions.

        @el.find(".capa_inputtype").each (index, inputtype) =>
            classes = $(inputtype).attr('class').split(' ')
            for cls in classes
              display = @inputtypeDisplays[$(inputtype).attr('id')]
              showMethod = @inputtypeShowAnswerMethods[cls]
              showMethod(inputtype, display, answers) if showMethod?

        if MathJax?
          @el.find('.problem > div').each (index, element) =>
            MathJax.Hub.Queue ["Typeset", MathJax.Hub, element]

        @$('.show-label').text 'Hide Answer(s)'
        @el.addClass 'showed'
        @updateProgress response
    else
      @$('[id^=answer_], [id^=solution_]').text ''
      @$('[correct_answer]').attr correct_answer: null
      @el.removeClass 'showed'
      @$('.show-label').text 'Show Answer(s)'

      @el.find(".capa_inputtype").each (index, inputtype) =>
        display = @inputtypeDisplays[$(inputtype).attr('id')]
        classes = $(inputtype).attr('class').split(' ')
        for cls in classes
          hideMethod = @inputtypeHideAnswerMethods[cls]
          hideMethod(inputtype, display) if hideMethod?

  gentle_alert: (msg) =>
    if @el.find('.capa_alert').length
      @el.find('.capa_alert').remove()
    alert_elem = "<div class='capa_alert'>" + msg + "</div>"
    @el.find('.action').after(alert_elem)
    @el.find('.capa_alert').css(opacity: 0).animate(opacity: 1, 700)

  save: =>
    Logger.log 'problem_save', @answers
    $.postWithPrefix "#{@url}/problem_save", @answers, (response) =>
      saveMessage = response.msg
      @gentle_alert saveMessage
      @updateProgress response

  refreshMath: (event, element) =>
    element = event.target unless element
    elid = element.id.replace(/^input_/,'')
    target = "display_" + elid

    # MathJax preprocessor is loaded by 'setupInputTypes'
    preprocessor_tag = "inputtype_" + elid
    mathjax_preprocessor = @inputtypeDisplays[preprocessor_tag]

    if MathJax? and jax = MathJax.Hub.getAllJax(target)[0]
      eqn = $(element).val()
      if mathjax_preprocessor
        eqn = mathjax_preprocessor(eqn)
      MathJax.Hub.Queue(['Text', jax, eqn], [@updateMathML, jax, element])

    return # Explicit return for CoffeeScript

  updateMathML: (jax, element) =>
    try
      $("##{element.id}_dynamath").val(jax.root.toMathML '')
    catch exception
      throw exception unless exception.restart
      if MathJax?
        MathJax.Callback.After [@refreshMath, jax], exception.restart

  refreshAnswers: =>
    @$('input.schematic').each (index, element) ->
      element.schematic.update_value()
    @$(".CodeMirror").each (index, element) ->
      element.CodeMirror.save() if element.CodeMirror.save
    @answers = @inputs.serialize()

  bindResetCorrectness: ->
    # Loop through all input types
    # Bind the reset functions at that scope.
    $inputtypes = @el.find(".capa_inputtype").add(@el.find(".inputtype"))
    $inputtypes.each (index, inputtype) =>
      classes = $(inputtype).attr('class').split(' ')
      for cls in classes
        bindMethod = @bindResetCorrectnessByInputtype[cls]
        if bindMethod?
          bindMethod(inputtype)

  # Find all places where each input type displays its correct-ness
  # Replace them with their original state--'unanswered'.
  bindResetCorrectnessByInputtype:
    # These are run at the scope of the capa inputtype
    # They should set handlers on each <input> to reset the whole.
    formulaequationinput: (element) ->
      $(element).find('input').on 'input', ->
        $p = $(element).find('p.status')
        $p.text gettext("unanswered")
        $p.parent().removeClass().addClass "unanswered"

    choicegroup: (element) ->
      $element = $(element)
      id = ($element.attr('id').match /^inputtype_(.*)$/)[1]
      $element.find('input').on 'change', ->
        $status = $("#status_#{id}")
        if $status[0]  # We found a status icon.
          $status.removeClass().addClass "unanswered"
          $status.empty().css 'display', 'inline-block'
        else
          # Recreate the unanswered dot on left.
          $("<span>", {"class": "unanswered", "style": "display: inline-block;", "id": "status_#{id}"})

        $element.find("label").removeClass()

    'option-input': (element) ->
      $select = $(element).find('select')
      id = ($select.attr('id').match /^input_(.*)$/)[1]
      $select.on 'change', ->
        $status = $("#status_#{id}")
          .removeClass().addClass("unanswered")
          .find('span').text(gettext('Status: unsubmitted'))

    textline: (element) ->
      $(element).find('input').on 'input', ->
        $p = $(element).find('p.status')
        $p.text "unanswered"
        $p.parent().removeClass().addClass "unanswered"

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

      input_id = element.attr('id').replace(/inputtype_/,'')
      answer = answers[input_id]
      for choice in answer
        element.find("label[for='input_#{input_id}_#{choice}']").addClass 'choicegroup_correct'

    javascriptinput: (element, display, answers) =>
      answer_id = $(element).attr('id').split("_")[1...].join("_")
      answer = JSON.parse(answers[answer_id])
      display.showAnswer(answer)

    choicetextgroup: (element, display, answers) =>
      element = $(element)

      input_id = element.attr('id').replace(/inputtype_/,'')
      answer = answers[input_id]
      for choice in answer
        element.find("section#forinput#{choice}").addClass 'choicetextgroup_show_correct'

  inputtypeHideAnswerMethods:
    choicegroup: (element, display) =>
      element = $(element)
      element.find('label').removeClass('choicegroup_correct')

    javascriptinput: (element, display) =>
      display.hideAnswer()

    choicetextgroup: (element, display) =>
      element = $(element)
      element.find("section[id^='forinput']").removeClass('choicetextgroup_show_correct')
