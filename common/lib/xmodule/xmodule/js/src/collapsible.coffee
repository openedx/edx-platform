class @Collapsible

  # Set of library functions that provide a simple way to add collapsible
  # functionality to elements. 

  # setCollapsibles:
  #   Scan element's content for generic collapsible containers
  @setCollapsibles: (el) =>
    ###
    el: container
    ###
    # standard longform + shortfom pattern
    el.find('.longform').hide()
    el.find('.shortform').append('<a href="#" class="full">See full output</a>')

    # custom longform + shortform text pattern
    short_custom = el.find('.shortform-custom') 
    # set up each one individually
    short_custom.each (index, elt) =>
      open_text = $(elt).data('open-text')
      close_text = $(elt).data('close-text')
      $(elt).append("<a href='#' class='full-custom'>"+ open_text + "</a>")
      $(elt).find('.full-custom').click (event) => @toggleFull(event, open_text, close_text)

    # collapsible pattern
    el.find('.collapsible header + section').hide()

    # set up triggers
    el.find('.full').click (event) => @toggleFull(event, "See full output", "Hide output")
    el.find('.collapsible header a').click @toggleHint

  @toggleFull: (event, open_text, close_text) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
    if $(event.target).text() == open_text
      new_text = close_text
    else
      new_text = open_text
    $(event.target).text(new_text)

  @toggleHint: (event) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
