class CMS.Views.SubtitlesImport extends Backbone.View
  tagName: 'div'
  className: 'comp-subtitles-entry'
  urlYT: "/import_subtitles"

  events:
    "click #import-from-youtube": 'clickImportFromYoutube'

  initialize: ->
    _.bindAll(@)
    @id = @$el.closest('.component').data('id')
    @msg =
      success:
        intent: 'confirmation'
        title: gettext("Subtitles were successfully imported.")
        actions:
          primary:
            text: gettext("Ok")
            click: (view, e) ->
              view.hide()
              e.preventDefault()
      warn:
        intent: 'warning'
        title: gettext("Are you sure that you want to import the subtitle file found on YouTube?")
        message: gettext("If subtitles for the video already exist, importing again will overwrite them.")
        actions:
          primary:
            text: gettext("Yes")
            click: @importFromYoutubeHandler

          secondary: [
            text: gettext("No")
            click: (view, e) ->
              view.hide()
              e.preventDefault()
          ]
      wait:
        intent: 'warning'
        title: gettext("Please wait for the subtitles to download")
        message: '''
          <div id="circle-preloader">
            <div id="circle-preloader_1" class="circle-preloader"></div>
            <div id="circle-preloader_2" class="circle-preloader"></div>
            <div id="circle-preloader_3" class="circle-preloader"></div>
          </div>
        '''
      error:
        intent: 'error'
        title: gettext("Import failed!")
        actions:
          primary:
            text: gettext("Ok")
            click: (view, e) ->
              view.hide()
              e.preventDefault()
    @showImportVariants()

  render: (type, params = {}) ->
    tpl = @options.tpl[type];
    if not tpl
        console.error("Couldn't load #{tpl[type]} template")
        return
    @$el.html(tpl(params))

  showPrompt: (type, data) ->
    msg =  @msg[type] || {}
    options = $.extend({}, CMS.Views.Prompt.prototype.options, msg)
    prompt = new CMS.Views.Prompt(options)
    prompt.show()

  showWarnMessage: ->
    @showPrompt('warn')

  showWaitMessage: ->
    @showPrompt('wait')

  showSuccessMessage: ->
    @showPrompt('success')

  showErrorMessage: (data)->
    type = 'error'
    options = data || {}
    @showPrompt('error', options)

  showImportVariants: ->
    @render('variants')

  clickImportFromYoutube: (event) ->
    event.preventDefault()
    @showWarnMessage()

  importFromYoutubeHandler: (view, event)->
      @importFromYoutube()
      event.preventDefault()

  xhrSuccessHandler: (data) ->
    if data.status is 'success'
      @showSuccessMessage()
    else
      @showErrorMessage(data)

  xhrErrorHandler: (data) ->
    @showErrorMessage({
      title: gettext("Import failed!")
      message: gettext("Problems with connection.")
    })

  importFromYoutube: ->
    @showWaitMessage()
    $.ajax(
          url: @urlYT
          type: "POST"
          dataType: "json"
          contentType: "application/json"
          timeout: 1000*60
          data: JSON.stringify(
              'id': @id
          )
      )
      .success(@xhrSuccessHandler)
      .error(@xhrErrorHandler)
