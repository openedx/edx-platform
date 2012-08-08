if not @Discussion?
  @Discussion = {}

Discussion = @Discussion


@Discussion = $.extend @Discussion,

  newPostTemplate: """
    <form class="new-post-form" _id="{{discussion_id}}">
      <ul class="discussion-errors new-post-form-error"></ul>    
      <input type="text" class="new-post-title title-input" placeholder="Title"/>
      <div class="new-post-similar-posts-wrapper" style="display: none">
        Similar Posts: 
        <a class="hide-similar-posts" href="javascript:void(0)">Hide</a>
        <div class="new-post-similar-posts"></div>
      </div>
      <div class="new-post-body body-input"></div>
      <input class="new-post-tags" placeholder="Tags"/>
      <div class = "new-post-control">
        <a class="discussion-cancel-post" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-post control-button" href="javascript:void(0)">Submit</a>
      </div>
    </form>
  """

  replyTemplate: """
    <form class="discussion-reply-new">
      <ul class="discussion-errors"></ul>
      <div class="reply-body"></div>
      <input type="checkbox" class="discussion-post-anonymously" id="discussion-post-anonymously-{{id}}" />
      <label for="discussion-post-anonymously-{{id}}">post anonymously</label>
      {{#showWatchCheckbox}}
      <input type="checkbox" class="discussion-auto-watch" id="discussion-autowatch-{{id}}" checked />
      <label for="discussion-auto-watch-{{id}}">follow this thread</label>
      {{/showWatchCheckbox}}
      <br />
      <div class = "reply-post-control">
        <a class="discussion-cancel-post" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-post control-button" href="javascript:void(0)">Submit</a>
      </div>
    </form>
  """

  editThreadTemplate: """
    <form class="discussion-content-edit discussion-thread-edit" _id="{{id}}">
      <ul class="discussion-errors discussion-update-errors"></ul>    
      <input type="text" class="thread-title-edit title-input" placeholder="Title" value="{{title}}"/>
      <div class="thread-body-edit body-input">{{body}}</div>
      <input class="thread-tags-edit" placeholder="Tags" value="{{tags}}" />
      <div class = "edit-post-control">
        <a class="discussion-cancel-update" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-update control-button" href="javascript:void(0)">Update</a>
      </div>
    </form>
  """

  editCommentTemplate: """
    <form class="discussion-content-edit discussion-comment-edit" _id="{{id}}">
      <ul class="discussion-errors discussion-update-errors"></ul>    
      <div class="comment-body-edit body-input">{{body}}</div>
      <div class = "edit-post-control">
        <a class="discussion-cancel-update" href="javascript:void(0)">Cancel</a>
        <a class="discussion-submit-update control-button" href="javascript:void(0)">Update</a>
      </div>
    </form>
  """
