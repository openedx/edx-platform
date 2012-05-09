class window.Courseware
  constructor: ->
    new CoursewareNavigation
    new Calculator
    new FeedbackForm
    Logger.bind()
    @renderModules()

  @start: ->
    new Courseware

  renderModules: ->
    $('.course-content .video').each ->
      id = $(this).attr('id').replace(/video_/, '')
      new Video id, $(this).data('streams')
