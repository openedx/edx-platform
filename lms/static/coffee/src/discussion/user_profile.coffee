if not @Discussion?
  @Discussion = {}

Discussion = @Discussion

@Discussion = $.extend @Discussion,
  initializeUserProfile: ($userProfile) ->
    $local = Discussion.generateLocal $userProfile

    handleUpdateModeratorStatus = (elem, isModerator) ->
      url = Discussion.urlFor('update_moderator_status', $$profiled_user_id)
      Discussion.safeAjax
        $elem: $(elem)
        url: url
        type: "POST"
        dataType: 'json'
        data:
          is_moderator: isModerator
        error: (response, textStatus, e) ->
          console.log e
        success: (response, textStatus) ->
          parent = $userProfile.parent()
          $userProfile.replaceWith(response.html)
          Discussion.initializeUserProfile parent.children(".user-profile")

    Discussion.bindLocalEvents $local,
      "click .sidebar-revoke-moderator-button": (event) ->
        handleUpdateModeratorStatus(this, false)
      "click .sidebar-promote-moderator-button": (event) ->
        handleUpdateModeratorStatus(this, true)
