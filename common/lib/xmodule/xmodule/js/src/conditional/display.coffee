class @Conditional

  constructor: (element) ->
    @el = $(element).find('.conditional-wrapper')

    if @el.data('conditional_module_processed') is 'true'
      console.log 'Conditional already processed this element'

    console.log 'Conditional processing this element for the first time.'
    @el.data 'conditional_module_processed', 'true'

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
      @el.append(i) for i in content
      XModule.loadModules(@el)
    else
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        console.log response
        @el.append(i) for i in response.html
        XModule.loadModules(@el)

