$ ->

  window.$$contents = {}
  window.$$discussions = {}

  $("section.discussion").each (index, elem) ->
    discussionData = DiscussionUtil.getDiscussionData($(elem).attr("_id"))
    discussion = new Discussion()
    discussion.reset(discussionData, {silent: false})
    view = new DiscussionView(el: elem, model: discussion)

  if window.$$annotated_content_info?
    DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)

  $userProfile = $(".discussion-sidebar>.user-profile")
  if $userProfile.length
    console.log "initialize user profile"
    view = new DiscussionUserProfileView(el: $userProfile[0])
