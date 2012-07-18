class @Courseware
  @prefix: ''

  constructor: ->
    Courseware.prefix = $("meta[name='path_prefix']").attr('content')
    new Navigation
    Logger.bind()
    @bind()
    @render()

  @start: ->
    new Courseware

  bind: ->
    $('.course-content .sequence, .course-content .tab')
      .bind 'contentChanged', @render

  render: ->
    $('.course-content .video').each (idx, element) -> new Video element
    $('.course-content .problems-wrapper').each (idx, element) -> new Problem element
    $('.course-content .histogram').each ->
      id = $(this).attr('id').replace(/histogram_/, '')
      new Histogram id, $(this).data('histogram')
