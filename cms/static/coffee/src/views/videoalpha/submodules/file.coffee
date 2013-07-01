class CMS.Views.SubtitlesImportFile extends Backbone.View
  tagName: "li"
  className: "import-file"
  link_id: "import-from-file"
  url: "/upload_subtitles"
  files: null

  events:
    "click #import-from-file": "clickHandler"
    "change .file-input": "changeHadler"

  initialize: ->
    _.bindAll(@)
    @messages = @options.msg
    @render()

  render: ->
    container = @options.$container
    tpl = @options.tpl.file if @options.tpl

    if not tpl
        console.error("Couldn't load template for file uploader")
        return

    @$el.append(
        $('<a></a>',
            class: "blue-button"
            id: @link_id
            href: "#"
        )
        .text(gettext("Upload from file"))
    )
    .append(tpl(
      component_id: @options.component_id
    ))
    .appendTo(container)

    @$form = container.find('.file-upload')
    @$fileInput = @$form.find('.file-input')

  clickHandler: (event) ->
    event.preventDefault()
    @$fileInput
      .val(null)
      .trigger('click')

  changeHadler: (event) ->
    event.preventDefault()
    @files = @$fileInput.get(0).files
    @messages.render('warn',
      title: gettext("Are you sure that you want to upload the subtitle file?")
      actions:
        primary:
          click: @importHandler
    )

  importHandler: (view, event) ->
    event.preventDefault()
    @import()

  import: ->
    if @files.length is 0
        return

    @$form.find('.file-chooser').ajaxSubmit(
        beforeSend: @xhrResetProgressBar
        uploadProgress: @xhrProgressHandler
        complete: @xhrCompleteHandler
    )

  xhrResetProgressBar: ->
    @messages.render(null,
      intent: 'warning'
      title: gettext("Uploading...")
      message: """
        <span class=\"file-name\">#{@files[0].name}</span>
        <span class=\"progress-bar\">
            <span class=\"progress-fill\"></span>
        </span>
      """
    )
    @$progressFill = @messages.findEl('.progress-fill')

  xhrProgressHandler: (event, position, total, percentComplete) ->
    percentVal = percentComplete + '%'
    @$progressFill
      .width(percentVal)
      .html(percentVal)

  xhrCompleteHandler: (xhr) ->
    resp = JSON.parse(xhr.responseText)
    if xhr.status is 200 and resp.success is true
        @messages.render('success')
    else
        @messages.render('error')
