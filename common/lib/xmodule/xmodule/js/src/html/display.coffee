class @HTMLModule

  constructor: (@element) ->
    @el = $(@element)
    @setCollapsibles()
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, @el[0]]

  $: (selector) ->
    $(selector, @el)

  setCollapsibles: =>
    $('.longform').hide();
    $('.shortform').append('<a href="#" class="full">See full output</a>');
    $('.collapsible section').hide();
    $('.full').click @toggleFull
    $('.collapsible header a').click @toggleHint

  toggleFull: (event) =>
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')
    text = $(event.target).text() == 'See full output' ? 'Hide output' : 'See full output'
    $(this).text(text)

  toggleHint: (event) =>
    event.preventDefault()
    $(event.target).parent().siblings().slideToggle()
    $(event.target).parent().parent().toggleClass('open')