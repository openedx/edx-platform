class CMS.Views.DownloadSubtitles extends Backbone.View
  tagName: "li"
  className: "download-file"
  link_id: "download-file"
  url: "/download_subtitles"

  initialize: ->
    _.bindAll(@)
    @messages = @options.msg
    @render()

  render: ->
    if @options.subtitlesExist is true
      id = encodeURIComponent(@options.component_id)
      html = @$el.append(
          $('<a></a>',
              class: "blue-button"
              id: @link_id
              href: "#{@url}?id=#{id}"
          )
          .text(gettext("Download subtitles"))
      )
      .appendTo(@options.$container)
