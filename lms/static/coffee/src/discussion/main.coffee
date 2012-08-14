$ ->

  toggle = ->
    $('.course-wrapper').toggleClass('closed')

  Discussion = window.Discussion
  if $('#accordion').length
    active = $('#accordion ul:has(li.active)').index('#accordion ul')
    $('#accordion').bind('accordionchange', @log).accordion
      active: if active >= 0 then active else 1
      header: 'h3'
      autoHeight: false
    $('#open_close_accordion a').click toggle
    $('#accordion').show()

  $(".discussion-module").each (index, elem) ->
    Discussion.initializeDiscussionModule(elem)

  $("section.discussion").each (index, discussion) ->
    Discussion.initializeDiscussion(discussion)
    Discussion.bindDiscussionEvents(discussion)

  Discussion.initializeUserProfile($(".discussion-sidebar>.user-profile"))
