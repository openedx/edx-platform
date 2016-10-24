class @Sequence
  constructor: (element) ->
    @updatedProblems = {}
    @requestToken = $(element).data('request-token')
    @el = $(element).find('.sequence')
    @path = $('.path')
    @contents = @$('.seq_contents')
    @content_container = @$('#seq_content')
    @sr_container = @$('.sr-is-focusable')
    @num_contents = @contents.length
    @id = @el.data('id')
    @ajaxUrl = @el.data('ajax-url')
    @nextUrl = @el.data('next-url')
    @prevUrl = @el.data('prev-url')
    @base_page_title = " | " + document.title
    @initProgress()
    @bind()
    @render parseInt(@el.data('position'))

  $: (selector) ->
    $(selector, @el)

  bind: ->
    @$('#sequence-list .nav-item').click @goto
    @el.on 'bookmark:add', @addBookmarkIconToActiveNavItem
    @el.on 'bookmark:remove', @removeBookmarkIconFromActiveNavItem
    @$('#sequence-list .nav-item').on('focus mouseenter', @displayTabTooltip)
    @$('#sequence-list .nav-item').on('blur mouseleave', @hideTabTooltip)

  displayTabTooltip: (event) =>
    $(event.currentTarget).find('.sequence-tooltip').removeClass('sr')

  hideTabTooltip: (event) =>
    $(event.currentTarget).find('.sequence-tooltip').addClass('sr')

  initProgress: ->
    @progressTable = {}  # "#problem_#{id}" -> progress

  updatePageTitle: ->
    # update the page title to include the current section
    position_link = @link_for(@position)
    if position_link and position_link.data('page-title')
        document.title = position_link.data('page-title') + @base_page_title

  hookUpContentStateChangeEvent: ->
    $('.problems-wrapper').bind(
      'contentChanged',
      (event, problem_id, new_content_state) =>
        @addToUpdatedProblems problem_id, new_content_state
    )

  addToUpdatedProblems: (problem_id, new_content_state) =>
    # Used to keep updated problem's state temporarily.
    # params:
    #   'problem_id' is problem id.
    #   'new_content_state' is updated problem's state.

    # initialize for the current sequence if there isn't any updated problem
    # for this position.
    if not @anyUpdatedProblems @position
      @updatedProblems[@position] = {}

    # Now, put problem content against problem id for current active sequence.
    @updatedProblems[@position][problem_id] = new_content_state

  anyUpdatedProblems:(position) ->
    # check for the updated problems for given sequence position.
    # params:
    #   'position' can be any sequence position.
    return @updatedProblems[position] != undefined

  hookUpProgressEvent: ->
    $('.problems-wrapper').bind 'progressChanged', @updateProgress

  mergeProgress: (p1, p2) ->
    # if either is "NA", return the other one
    if p1 == "NA"
      return p2
    if p2 == "NA"
      return p1

    # Both real progresses
    if p1 == "done" and p2 == "done"
      return "done"

    # not done, so if any progress on either, in_progress
    w1 = p1 == "done" or p1 == "in_progress"
    w2 = p2 == "done" or p2 == "in_progress"
    if w1 or w2
      return "in_progress"

    return "none"

  updateProgress: =>
    new_progress = "NA"
    _this = this
    $('.problems-wrapper').each (index) ->
      progress = $(this).data 'progress_status'
      new_progress = _this.mergeProgress progress, new_progress

    @progressTable[@position] = new_progress

  enableButton: (button_class, button_action) ->
    @$(button_class).removeClass('disabled').removeAttr('disabled').click(button_action)

  disableButton: (button_class) ->
    @$(button_class).addClass('disabled').attr('disabled', true)

  setButtonLabel: (button_class, button_label) ->
    @$(button_class + ' .sr').html(button_label)

  updateButtonState: (button_class, button_action, action_label_prefix, is_at_boundary, boundary_url) ->
    if is_at_boundary and boundary_url == 'None'
      @disableButton(button_class)
    else
      button_label = action_label_prefix + (if is_at_boundary then ' Subsection' else ' Unit')
      @setButtonLabel(button_class, button_label)
      @enableButton(button_class, button_action)

  toggleArrows: =>
    @$('.sequence-nav-button').unbind('click')

    # previous button
    is_first_tab = @position == 1
    previous_button_class = '.sequence-nav-button.button-previous'
    @updateButtonState(
      previous_button_class,  # bound element
      @selectPrevious,  # action
      'Previous',  # label prefix
      is_first_tab,  # is boundary?
      @prevUrl  # boundary_url
    )

    # next button
    is_last_tab = @position >= @contents.length  # use inequality in case contents.length is 0 and position is 1.
    next_button_class = '.sequence-nav-button.button-next'
    @updateButtonState(
      next_button_class,  # bound element
      @selectNext,  # action
      'Next',  # label prefix
      is_last_tab,  # is boundary?
      @nextUrl  # boundary_url
    )

  render: (new_position) ->
    if @position != new_position
      if @position != undefined
        @mark_visited @position
        modx_full_url = "#{@ajaxUrl}/goto_position"
        $.postWithPrefix modx_full_url, position: new_position

      # On Sequence change, fire custom event "sequence:change" on element.
      # Added for aborting video bufferization, see ../video/10_main.js
      @el.trigger "sequence:change"
      @mark_active new_position

      current_tab = @contents.eq(new_position - 1)

      bookmarked = if @el.find('.active .bookmark-icon').hasClass('bookmarked') then true else false
      @content_container.html(current_tab.text()).attr("aria-labelledby", current_tab.attr("aria-labelledby")).data('bookmarked', bookmarked)

      # update the data-attributes with latest contents only for updated problems.
      if @anyUpdatedProblems new_position
        $.each @updatedProblems[new_position], (problem_id, latest_content) =>
          @content_container
          .find("[data-problem-id='#{ problem_id }']")
          .data('content', latest_content)

      XBlock.initializeBlocks(@content_container, @requestToken)

      window.update_schematics() # For embedded circuit simulator exercises in 6.002x

      @position = new_position
      @toggleArrows()
      @hookUpContentStateChangeEvent()
      @hookUpProgressEvent()
      @updatePageTitle()

      sequence_links = @content_container.find('a.seqnav')
      sequence_links.click @goto

      @path.text(@el.find('.nav-item.active').data('path'))

      @sr_container.focus()

  goto: (event) =>
    event.preventDefault()
    if $(event.currentTarget).hasClass 'seqnav' # Links from courseware <a class='seqnav' href='n'>...</a>, was .target
      new_position = $(event.currentTarget).attr('href')
    else # Tab links generated by backend template
      new_position = $(event.currentTarget).data('element')

    if (1 <= new_position) and (new_position <= @num_contents)
      is_bottom_nav = $(event.target).closest('nav[class="sequence-bottom"]').length > 0
      if is_bottom_nav
        widget_placement = 'bottom'
      else
        widget_placement = 'top'
      Logger.log "edx.ui.lms.sequence.tab_selected",  # Formerly known as seq_goto
        current_tab: @position
        target_tab: new_position
        tab_count: @num_contents
        id: @id
        widget_placement: widget_placement

      # On Sequence change, destroy any existing polling thread
      # for queued submissions, see ../capa/display.js
      if window.queuePollerID
        window.clearTimeout(window.queuePollerID)
        delete window.queuePollerID

      @render new_position
    else
      alert_template = gettext("Sequence error! Cannot navigate to %(tab_name)s in the current SequenceModule. Please contact the course staff.")
      alert_text = interpolate(alert_template, {tab_name: new_position}, true)
      alert alert_text

  selectNext: (event) => @_change_sequential 'next', event

  selectPrevious: (event) => @_change_sequential 'previous', event

  # `direction` can be 'previous' or 'next'
  _change_sequential: (direction, event) =>
    # silently abort if direction is invalid.
    return unless direction in ['previous', 'next']

    event.preventDefault()

    analytics_event_name = "edx.ui.lms.sequence.#{direction}_selected"
    is_bottom_nav = $(event.target).closest('nav[class="sequence-bottom"]').length > 0

    if is_bottom_nav
      widget_placement = 'bottom'
    else
      widget_placement = 'top'

    Logger.log analytics_event_name,  # Formerly known as seq_next and seq_prev
      id: @id
      current_tab: @position
      tab_count: @num_contents
      widget_placement: widget_placement

    if (direction == 'next') and (@position >= @contents.length)
      window.location.href = @nextUrl
    else if (direction == 'previous') and (@position == 1)
      window.location.href = @prevUrl
    else
      # If the bottom nav is used, scroll to the top of the page on change.
      if is_bottom_nav 
        $.scrollTo 0, 150
      offset =
        next: 1
        previous: -1
      new_position = @position + offset[direction]
      @render new_position

  link_for: (position) ->
    @$("#sequence-list .nav-item[data-element=#{position}]")

  mark_visited: (position) ->
    # Don't overwrite class attribute to avoid changing Progress class
    element = @link_for(position)
    element.removeClass("inactive")
    .removeClass("active")
    .addClass("visited")

  mark_active: (position) ->
    # Don't overwrite class attribute to avoid changing Progress class
    element = @link_for(position)
    element.removeClass("inactive")
    .removeClass("visited")
    .addClass("active")

  addBookmarkIconToActiveNavItem: (event) =>
    event.preventDefault()
    @el.find('.nav-item.active .bookmark-icon').removeClass('is-hidden').addClass('bookmarked')
    @el.find('.nav-item.active .bookmark-icon-sr').text(gettext('Bookmarked'))

  removeBookmarkIconFromActiveNavItem: (event) =>
    event.preventDefault()
    @el.find('.nav-item.active .bookmark-icon').removeClass('bookmarked').addClass('is-hidden')
    @el.find('.nav-item.active .bookmark-icon-sr').text('')
