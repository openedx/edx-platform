class @JavascriptLoader
  ###
  Set of library functions that provide common interface for javascript loading
  for all module types
  ###
  @setCollapsibles: (el) =>
    ###
    el: jQuery object representing xmodule
    ###
    el.find('.longform').hide();
    el.find('.shortform').append('<a href="#" class="full">See full output</a>');
    el.find('.collapsible section').hide();
    el.find('.full').click @toggleFull
    el.find('.collapsible header a').click @toggleHint

  @toggleFull: (event) =>
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
    text = $(event.target).text() == 'See full output' ? 'Hide output' : 'See full output'
    $(this).text(text)

  @toggleHint: (event) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
