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
      $('#seq_content').change @render

  render: ->
    $('.course-content .video').each ->
      id = $(this).attr('id').replace(/video_/, '')
      new Video id, $(this).data('streams')
