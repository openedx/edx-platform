class @Hinter
  # The client side code for the crowdsource_hinter.
  # Contains code for capturing problem checks and making ajax calls to
  # the server component.  Also contains styling code to clear default
  # text on a textarea.

  constructor: (element) ->
    @el = $(element).find('.crowdsource-wrapper')
    @url = @el.data('url')
    Logger.listen('problem_graded', @el.data('child-url'), @capture_problem)
    @render()

  capture_problem: (event_type, data, element) =>
    # After a problem gets graded, we get the info here.
    # We want to send this info to the server in another AJAX
    # request.
    answers = data[0]
    response = data[1]
    if response.search(/class="correct/) == -1
      # Incorrect.  Get hints.
      $.postWithPrefix "#{@url}/get_hint", answers, (response) =>
        @render(response.contents)
    else
      # Correct.  Get feedback from students.
      $.postWithPrefix "#{@url}/get_feedback", answers, (response) =>
        @render(response.contents)

  $: (selector) ->
    $(selector, @el)

  jq_escape: (string) =>
    # Escape a string for jquery selector use.
    return string.replace(/[!"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, '\\$&')

  bind: =>
    @$('input.vote').click @vote
    @$('input.submit-hint').click @submit_hint
    @$('.custom-hint').click @clear_default_text
    @$('#answer-tabs').tabs({active: 0})
    @$('.expand').click @expand

  expand: (eventObj) =>
    target = @$('#' + @$(eventObj.currentTarget).data('target'))
    if @$(target).css('display') == 'none'
      @$(target).css('display', 'block')
    else
      @$(target).css('display', 'none')

  vote: (eventObj) =>
    target = @$(eventObj.currentTarget)
    all_pks = @$('#pk-list').attr('data-pk-list')
    post_json = {'answer': target.attr('data-answer'), 'hint': target.data('hintno'), 'pk_list': all_pks}
    $.postWithPrefix "#{@url}/vote", post_json, (response) =>
      @render(response.contents)

  submit_hint: (eventObj) =>
    textarea = $('.custom-hint')
    answer = $('input:radio[name=answer-select]:checked').val()
    if answer == undefined
      # The user didn't choose an answer.  Do nothing.
      return
    post_json = {'answer': answer, 'hint': textarea.val()}
    $.postWithPrefix "#{@url}/submit_hint",post_json, (response) =>
      @render(response.contents)

  clear_default_text: (eventObj) =>
    target = @$(eventObj.currentTarget)
    if target.data('cleared') == undefined
      target.val('')
      target.data('cleared', true)

  render: (content) ->
    if content
      # Trim leading and trailing whitespace
      content = content.replace /^\s+|\s+$/g, ""

    if content
      @el.html(content)
      @el.show()
      JavascriptLoader.executeModuleScripts @el, () =>
        @bind()
      @$('#previous-answer-0').css('display', 'inline')
    else
      @el.hide()
