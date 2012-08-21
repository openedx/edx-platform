$ ->

  $(".discussion-module").each (index, elem) ->
    view = new DiscussionModuleView(el: elem)

  $("section.discussion").each (index, elem) ->
    discussionData = DiscussionUtil.getDiscussionData(elem)
    discussion = new Discussion()
    discussion.reset(discussionData, {silent: false})
    view = new DiscussionView(el: elem, model: discussion)
