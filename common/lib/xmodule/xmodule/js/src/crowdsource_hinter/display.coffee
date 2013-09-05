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

  bind: =>
    @$('input.vote').click @vote
    @$('input.submit-hint').click @submit_hint
    @$('.custom-hint').click @clear_default_text
    @$('.expand').click @expand
    @$('.wizard-link').click @wizard_link_handle
    @$('.answer-choice').click @answer_choice_handle

  expand: (eventObj) =>
    # Expand a hidden div.
    target = @$('#' + @$(eventObj.currentTarget).data('target'))
    if @$(target).css('display') == 'none'
      @$(target).css('display', 'block')
    else
      @$(target).css('display', 'none')
    # Fix positioning errors with the bottom class.
    @set_bottom_links()

  vote: (eventObj) =>
    # Make an ajax request with the user's vote.
    target = @$(eventObj.currentTarget)
    all_pks = @$('#pk-list').attr('data-pk-list')
    post_json = {'answer': target.attr('data-answer'), 'hint': target.data('hintno'), 'pk_list': all_pks}
    $.postWithPrefix "#{@url}/vote", post_json, (response) =>
      @render(response.contents)

  submit_hint: (eventObj) =>
    # Make an ajax request with the user's new hint.
    textarea = $('.custom-hint')
    if @answer == ''
      # The user didn't choose an answer, somehow.  Do nothing.
      return
    post_json = {'answer': @answer, 'hint': textarea.val()}
    $.postWithPrefix "#{@url}/submit_hint",post_json, (response) =>
      @render(response.contents)

  clear_default_text: (eventObj) =>
    # Remove placeholder text in the hint submission textbox.
    target = @$(eventObj.currentTarget)
    if target.data('cleared') == undefined
      target.val('')
      target.data('cleared', true)

  wizard_link_handle: (eventObj) =>
    # Move to another wizard view, based on the link that the user clicked.
    target = @$(eventObj.currentTarget)
    @go_to(target.attr('dest'))

  answer_choice_handle: (eventObj) =>
    # A special case of wizard_link_handle - we need to track a state variable,
    # the answer that the user chose.
    @answer = @$(eventObj.target).attr('value')
    @$('#blank-answer').html(@answer)
    @go_to('p3')

  set_bottom_links: =>
    # Makes each .bottom class stick to the bottom of .wizard-viewbox
    @$('.bottom').css('margin-top', '0px')
    viewbox_height = parseInt(@$('.wizard-viewbox').css('height'), 10)
    @$('.bottom').each((index, obj) ->
      view_height = parseInt($(obj).parent().css('height'), 10)
      $(obj).css('margin-top', (viewbox_height - view_height) + 'px')
    )

  render: (content) ->
    if content
      # Trim leading and trailing whitespace
      content = content.trim()

    if content
      @el.html(content)
      @el.show()
      JavascriptLoader.executeModuleScripts @el, () =>
        @bind()
      @$('#previous-answer-0').css('display', 'inline')
    else
      @el.hide()
    # Initialize the answer choice - remembers which answer the user picked on
    # p2 when he submits a hint on p3.
    @answer = ''
    # Determine whether the browser supports CSS3 transforms.
    styles = document.body.style
    if styles.WebkitTransform == '' or styles.transform == ''
      @go_to = @transform_go_to
    else
      @go_to = @legacy_go_to

    # Make the correct wizard view show up.
    hints_exist = @$('#hints-exist').html() == 'True'
    if hints_exist
      @go_to('p1')
    else
      @go_to('p2')

  transform_go_to: (view_id) ->
    # Switch wizard views using sliding transitions.
    id_to_index = {
      'p1': 0,
      'p2': 1,
      'p3': 2,
    }
    translate_string = 'translateX(' +id_to_index[view_id] * -1 * parseInt($('#' + view_id).css('width'), 10) + 'px)'
    @$('.wizard-container').css('transform', translate_string)
    @$('.wizard-container').css('-webkit-transform', translate_string)
    @set_bottom_links()

  legacy_go_to: (view_id) ->
    # For older browsers - switch wizard views by changing the screen.
    @$('.wizard-view').css('display', 'none')
    @$('#' + view_id).css('display', 'block')
    @set_bottom_links()