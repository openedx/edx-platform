class CMS.Views.SubtitlesImport extends Backbone.View
  tagName: "ul"
  className: "comp-subtitles-import-list"

  initialize: ->
    _.bindAll(@)
    @component_id = @options.container
      .closest(".component")
      .data('id')
    @messages = new @options["msg"]()

    @render()

  render: ->
    @$el.appendTo(@options.container)

    options = $.extend(true, {}, @options,
      component_id: @component_id
      msg: @messages
      $container: @$el
    )
    modules = @options.modules
    $.each modules, (index) ->
      new modules[index](options)