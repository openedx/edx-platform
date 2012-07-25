class @Courseware
  @prefix: ''

  constructor: ->
    Courseware.prefix = $("meta[name='path_prefix']").attr('content')
    new Navigation
    Logger.bind()
    @render()

  @start: ->
    new Courseware

  render: ->
    XModule.loadModules('display')
    $('.course-content .histogram').each ->
      id = $(this).attr('id').replace(/histogram_/, '')
      new Histogram id, $(this).data('histogram')
