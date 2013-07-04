class CMS.Views.SubtitlesImportYT extends Backbone.View
  tagName: "li"
  className: "import-youtube"
  link_id: "import-from-youtube"
  url: "/import_subtitles"
  files: null

  events:
    "click #import-from-youtube": "clickHandler"

  initialize: ->
    _.bindAll(@)
    @messages = @options.msg
    @render()

  render: ->
    html = @$el.append(
        $('<a></a>',
            class: "blue-button"
            id: @link_id
            href: "#"
        )
        .text(gettext("Import from Youtube"))
    )
    .appendTo(@options.$container)

  clickHandler: (event) ->
    event.preventDefault()
    @messages.render('warn',
      title: gettext('''
        Are you sure that you want to import the subtitle file
        found on YouTube?
      ''')
      actions:
        primary:
          click: @importHandler
    )

  importHandler: (view, event)->
      event.preventDefault()
      @import()

  xhrSuccessHandler: (data) ->
    if data.success is true
      @messages.render('success')
    else
      @xhrErrorHandler()

  xhrErrorHandler: ->
    @messages.render('error')

  import: ->
    @messages.render('wait')

    $.ajax(
          url: @url
          type: "POST"
          dataType: "json"
          contentType: "application/json"
          timeout: 1000*60
          data: JSON.stringify(
              'id': @options.component_id
          )
      )
      .success(@xhrSuccessHandler)
      .error(@xhrErrorHandler)
