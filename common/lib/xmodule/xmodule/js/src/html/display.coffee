class @HTMLModule

  constructor: (@element) ->
    @el = $(@element)
    JavascriptLoader.executeModuleScripts(@el)
    Collapsible.setCollapsibles(@el)

  $: (selector) ->
    $(selector, @el)
