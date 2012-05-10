class @Courseware
  constructor: ->
    new Navigation
    new Calculator
    new FeedbackForm
    Logger.bind()
    @bind()
    @render()

  @start: ->
    new Courseware

  bind: ->
    if $('#seq_content').length
      $('#seq_content').bind 'contentChanged', @render

  render: ->
    $('.course-content .video').each ->
      id = $(this).attr('id').replace(/video_/, '')
      new Video id, $(this).data('streams')
    $('.course-content .problems-wrapper').each ->
      id = $(this).attr('id').replace(/problem_/, '')
      new Problem id, $(this).data('url')
