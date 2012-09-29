class @JavascriptLoader
  ###
  Set of library functions that provide common interface for javascript loading
  for all module types
  ###
  @setCollapsibles: () =>
    console.log($('.collapsible section'))
    $('.longform').hide();
    $('.shortform').append('<a href="#" class="full">See full output</a>');
    $('.collapsible section').hide();
    $('.full').click @toggleFull
    $('.collapsible header a').click @toggleHint
    @toggleHint()

  @toggleFull: (event) =>
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
    text = $(event.target).text() == 'See full output' ? 'Hide output' : 'See full output'
    $(this).text(text)

  @toggleHint: (event) =>
    console.log('toggleHint')
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
