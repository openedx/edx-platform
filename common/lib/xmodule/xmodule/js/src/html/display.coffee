class @HTMLModule

  constructor: (@element) ->
    @el = $(@element)
    JavascriptLoader.executeModuleScripts(@el)
    JavascriptLoader.setCollapsibles(@el)

  $: (selector) ->
    $(selector, @el)
