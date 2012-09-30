class @JavascriptLoader

  # Set of library functions that provide common interface for javascript loading
  # for all module types. All functionality provided by JavascriptLoader should take
  # place at module scope, i.e. don't run jQuery over entire page

  # executeModuleScripts:
  #   Scan module contents for "script_placeholder"s, then:
  #     1) Fetch each script from server
  #     2) Explicitly attach the script to the <head> of document
  #     3) Explicitly wait for each script to be loaded
  #     4) Return to callback function when all scripts loaded
  @executeModuleScripts: (el, callback=null) ->
    console.log('executeModuleScripts')


  # setCollapsibles:
  #   Scan module contents for generic collapsible containers
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
