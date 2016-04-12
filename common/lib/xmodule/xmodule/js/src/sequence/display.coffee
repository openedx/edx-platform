class @Sequence
  constructor: (element) ->
    @requestToken = $(element).data('request-token')
    @el = $(element).find('.sequence')
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
    @setProgress(new_progress, @link_for(@position))

  setProgress: (progress, element) ->
      # If progress is "NA", don't add any css class
      element.removeClass('progress-none')
             .removeClass('progress-some')
             .removeClass('progress-done')

      switch progress
        when 'none' then element.addClass('progress-none')
        when 'in_progress' then element.addClass('progress-some')
        when 'done' then element.addClass('progress-done')

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
    first_tab = @position == 1
    previous_button_class = '.sequence-nav-button.button-previous'
    @updateButtonState(previous_button_class, @previous, 'Previous', first_tab, @prevUrl)

    # next button
    last_tab = @position >= @contents.length  # use inequality in case contents.length is 0 and position is 1.
    next_button_class = '.sequence-nav-button.button-next'
    @updateButtonState(next_button_class, @next, 'Next', last_tab, @nextUrl)

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
      XBlock.initializeBlocks(@content_container, @requestToken)

      window.update_schematics() # For embedded circuit simulator exercises in 6.002x

      @position = new_position
      @toggleArrows()
      @hookUpProgressEvent()
      @updatePageTitle()

      sequence_links = @content_container.find('a.seqnav')
      sequence_links.click @goto

      @el.find('.path').text(@el.find('.nav-item.active').data('path'))

      @sr_container.focus();

  goto: (event) =>
    event.preventDefault()
    if $(event.currentTarget).hasClass 'seqnav' # Links from courseware <a class='seqnav' href='n'>...</a>, was .target
      new_position = $(event.currentTarget).attr('href')
    else # Tab links generated by backend template
      new_position = $(event.currentTarget).data('element')

    if (1 <= new_position) and (new_position <= @num_contents)
      Logger.log "seq_goto", old: @position, new: new_position, id: @id

      # On Sequence change, destroy any existing polling thread
      # for queued submissions, see ../capa/display.coffee
      if window.queuePollerID
        window.clearTimeout(window.queuePollerID)
        delete window.queuePollerID

      @render new_position
    else
      alert_template = gettext("Sequence error! Cannot navigate to %(tab_name)s in the current SequenceModule. Please contact the course staff.")
      alert_text = interpolate(alert_template, {tab_name: new_position}, true)
      alert alert_text

  next: (event) => @_change_sequential 'seq_next', event
  previous: (event) => @_change_sequential 'seq_prev', event

  # `direction` can be 'seq_prev' or 'seq_next'
  _change_sequential: (direction, event) =>
    # silently abort if direction is invalid.
    return unless direction in ['seq_prev', 'seq_next']

    event.preventDefault()
    offset =
      seq_next: 1
      seq_prev: -1
    new_position = @position + offset[direction]
    Logger.log direction,
      old: @position
      new: new_position
      id: @id

    if (direction == "seq_next") and (@position == @contents.length)
      window.location.href = @nextUrl
    else if (direction == "seq_prev") and (@position == 1)
      window.location.href = @prevUrl
    else
      # If the bottom nav is used, scroll to the top of the page on change.
      if $(event.target).closest('nav[class="sequence-bottom"]').length > 0
        $.scrollTo 0, 150
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
