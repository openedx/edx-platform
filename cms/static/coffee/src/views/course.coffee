class CMS.Views.Course extends Backbone.View
  initialize: ->
    @$('#weeks > li').each (index, week) =>
      new CMS.Views.Week el: week, height: @maxWeekHeight()

    CMS.on('showContent', @showContent)
    CMS.on('hideContent', @hideContent)

  showContent: (subview) =>
    $('body').addClass('content')
    @$('.main-content').html(subview.el)
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
