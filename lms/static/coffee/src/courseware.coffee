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
    $('.course-content .video').each ->
      id = $(this).attr('id').replace(/video_/, '')
      new Video id, $(this).data('streams')
    $('.course-content .problems-wrapper').each ->
      id = $(this).attr('id').replace(/problem_/, '')
      new Problem id, $(this).data('url')
    $('.course-content .histogram').each ->
      id = $(this).attr('id').replace(/histogram_/, '')
      new Histogram id, $(this).data('histogram')
