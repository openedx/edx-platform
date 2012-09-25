if Backbone?
  class @DiscussionUserProfileView extends Backbone.View
    toggleModeratorStatus: (event) ->
      confirmValue = confirm("Are you sure?")
      if not confirmValue then return
      $elem = $(event.target)
      if $elem.hasClass("sidebar-promote-moderator-button")
        isModerator = true
      else if $elem.hasClass("sidebar-revoke-moderator-button")
        isModerator = false
      else
        console.error "unrecognized moderator status"
        return
      url = DiscussionUtil.urlFor('update_moderator_status', $$profiled_user_id)
      DiscussionUtil.safeAjax
        $elem: $elem
        url: url
        type: "POST"
        dataType: 'json'
        data:
          is_moderator: isModerator
        error: (response, textStatus, e) ->
          console.log e
        success: (response, textStatus) =>
          parent = @$el.parent()
          @$el.replaceWith(response.html)
          view = new DiscussionUserProfileView el: parent.children(".user-profile")

    events:
      "click .sidebar-toggle-moderator-button": "toggleModeratorStatus"
