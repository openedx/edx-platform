class CMS.Views.Course extends Backbone.View
  initialize: ->
    CMS.on('content.show', @showContent)
    CMS.on('content.hide', @hideContent)

  render: ->
    @$('#weeks > li').each (index, week) =>
      new CMS.Views.Week(el: week, height: @maxWeekHeight()).render()
    return @

  showContent: (subview) =>
    $('body').addClass('content')
    @$('.main-content').html(subview.render().el)
    @$('.cal').css height: @contentHeight()
    @$('>section').css minHeight: @contentHeight()

  hideContent: =>
    $('body').removeClass('content')
    @$('.main-content').empty()
    @$('.cal').css height: ''
    @$('>section').css minHeight: ''

  maxWeekHeight: ->
    _.max($('#weeks > li').map -> $(this).height()) + 1

  contentHeight: ->
    padding = 29
    $(window).height() - padding
