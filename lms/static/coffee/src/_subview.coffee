class @Subview
  constructor: (options) ->
    $.each options, (key, value) =>
      @[key] = value
    @initialize()
    @render()
    @bind()

  $: (selector) ->
    $(selector, @element)

  initialize: ->
  render: ->
  bind: ->
