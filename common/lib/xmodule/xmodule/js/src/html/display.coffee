class @HTMLModule

  constructor: (@element) ->
    @el = $(@element)
    JavascriptLoader.setCollapsibles(@el)

  $: (selector) ->
    $(selector, @el)
