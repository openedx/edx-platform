class @Conditional

  constructor: (element) ->
    @el = $(element).find('.conditional-wrapper')
    @id = @el.data('problem-id')
    @element_id = @el.attr('id')
    @url = @el.data('url')
    @render()

  $: (selector) ->
    $(selector, @el)

  updateProgress: (response) =>
    if response.progress_changed
        @el.attr progress: response.progress_status
        @el.trigger('progressChanged')

  render: (content) ->
    if content
      @el.html(content)
      XModule.loadModules('display', @el)
    else
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        @el.html(response.html)
        XModule.loadModules('display', @el)

