class @Collapsible

  # Set of library functions that provide a simple way to add collapsible
  # functionality to elements. 

  # setCollapsibles:
  #   Scan element's content for generic collapsible containers
  @setCollapsibles: (el) =>
    ###
    el: container
    ###
    el.find('.longform').hide()
    el.find('.shortform').append('<a href="#" class="full">See full output</a>')
    el.find('.collapsible header + section').hide()
    el.find('.full').click @toggleFull
    el.find('.collapsible header a').click @toggleHint

  @toggleFull: (event) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
    if $(event.target).text() == 'See full output'
      new_text = 'Hide output'
    else
      new_text = 'See full ouput'
    $(event.target).text(new_text)

  @toggleHint: (event) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
