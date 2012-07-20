$ ->

  DEBUG = true

  $(".discussion-title").click ->
    $thread = $(this).parent().children(".thread")
    if $thread.css("display") == "none"
      $thread.show()
    else
      $thread.hide()

  $(".thread-title").click ->
    $comments = $(this).parent().parent().children(".comments")
    if $comments.css("display") == "none"
      $comments.show()
    else
      $comments.hide()

  getDiscussionContentLink = ($elem, selector) ->
    $elem.children(".discussion-content-view").children(".info").children(selector)

  discussionContentHoverIn = ->
    status = $(this).attr("status") || "normal"
    if status == "normal"
      getDiscussionContentLink($(this), ".discussion-link").show()
    else if status == "reply"
      getDiscussionContentLink($(this), ".discussion-cancel-reply").show()
      getDiscussionContentLink($(this), ".discussion-submit-reply").show()
    else if status == "edit"
      getDiscussionContentLink($(this), ".discussion-cancel-edit").show()
      getDiscussionContentLink($(this), ".discussion-update-edit").show()

  discussionContentHoverOut = ->
    getDiscussionContentLink($(this), ".discussion-link").hide()

  $(".discussion-content").hover(discussionContentHoverIn, discussionContentHoverOut)

  $(".discussion-reply").click ->
    handleReply(this)

  $(".discussion-cancel-reply").click ->
    handleCancelReply(this)

  discussionLink = (cls, txt, handler) ->
    $("<a>").addClass("discussion-link").
             attr("href", "javascript:void(0)").
             addClass(cls).html(txt).
             click(-> handler(this))

  handleReply = (elem) ->
    discussionContent = $(elem).parents(".discussion-content")
    editView = discussionContent.children(".discussion-content-edit")
    if editView.length
      editView.show()
    else
      editView = $("<div>").addClass("discussion-content-edit")
      editView.append($("<textarea>").addClass("comment-edit"))
      $(elem).parents(".discussion-content").append(editView)
    cancelReply = discussionLink("discussion-cancel-reply", "Cancel", handleCancelReply)
    submitReply = discussionLink("discussion-submit-reply", "Submit", handleSubmitReply)
    $(elem).parents(".info").children(".discussion-link").hide()
    $(elem).after(submitReply).replaceWith(cancelReply)
    discussionContent.attr("status", "reply")

  handleCancelReply = (elem) ->
    discussionContent = $(elem).parents(".discussion-content")
    editView = discussionContent.children(".discussion-content-edit")
    if editView.length
      editView.hide()
    getDiscussionContentLink(discussionContent, ".discussion-submit-reply").remove()
    reply = discussionLink("discussion-reply", "Reply", handleReply)
    $(elem).parents(".info").children(".discussion-link").show()
    $(elem).replaceWith(reply)
    discussionContent.attr("status", "normal")

  urlFor = (name, param) ->
    {
      create_thread      : "TODO" # TODO
      update_thread      : "/discussions/threads/#{param}/update"
      create_comment     : "/discussions/threads/#{param}/reply"
      delete_thread      : "/discussions/threads/#{param}/delete"
      update_comment     : "/discussions/comments/#{param}/update"
      endorse_comment    : "/discussions/comments/#{param}/endorse"
      create_sub_comment : "/discussions/comments/#{param}/reply"
      delete_comment     : "/discussions/comments/#{param}/delete"
      upvote_comment     : "/discussions/comments/#{param}/upvote"
      downvote_comment   : "/discussions/comments/#{param}/downvote"
      upvote_thread      : "/discussions/threads/#{param}/upvote"
      downvote_thread    : "/discussions/threads/#{param}/downvote"
    }[name]

  renderComment = (comment) ->
    """
    <div class="comment" _id="#{comment['id']}">
      <div class="discussion-content">
        <div class="discussion-content-view">
          <div class="comment-body">#{comment['body']}</div>
          <div class="info">
            less than a minute ago by user No.#{comment['user_id']}
            <a class="discussion-link discussion-reply" href="javascript:void(0)">Reply</a>
            <a class="discussion-link discussion-edit" href="javascript:void(0)">Edit</a>
          </div>
        </div>
      </div>
      <div class="comments">
      </div>
    </div>
    """

  handleSubmitReply = (elem) ->
    $div = $(elem).parents(".discussion-content").parent()
    if $div.hasClass("thread")
      url = urlFor('create_comment', $div.attr("_id"))
    else if $div.hasClass("comment")
      url = urlFor('create_sub_comment', $div.attr("_id"))
    else
      return
    $edit = $div.children(".discussion-content").find(".comment-edit")
    body = $edit.val()
    $.post url, {body: body}, (response, textStatus) ->
      if textStatus == "success"
        if not DEBUG
          window.location = window.location.pathname + "#" + response['id']
          window.location.reload()
      console.log response
      console.log textStatus
    , 'json'

  handleSubmitNewThread = (elem) ->

  handleSubmitUpdate = (elem) ->

  handleSubmitVote = (elem) ->

  console.log window.location.pathname
