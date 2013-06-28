class CMS.Views.SubtitlesMessages extends  Backbone.View

  initialize: ->
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
        title: gettext("Are you sure that you want to import/upload the subtitle?")
        message: gettext("If subtitles for the video already exist, importing again will overwrite them.")
        actions:
          primary:
            text: gettext("Yes")

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
          <span id="circle-preloader">
            <span id="circle-preloader_1" class="circle-preloader"></span>
            <span id="circle-preloader_2" class="circle-preloader"></span>
            <span id="circle-preloader_3" class="circle-preloader"></span>
          </span>
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

  render: (type, data) ->
    msg =  @msg[type] || {}
    options = $.extend(true, {}, CMS.Views.Prompt.prototype.options, msg, data)
    @prompt = new CMS.Views.Prompt(options)
    @prompt.show()

  hide: (event) ->
    event.preventDefault() if event
    @prompt.hide()

  findEl: (selector) ->
    @prompt.$el.find(selector) if @prompt
