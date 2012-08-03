if not @Discussion?
  @Discussion = {}

Discussion = @Discussion


###
titleTemplate = """
  <a class="thread-title" name="{{id}}" href="javascript:void(0)">{{title}}</a>
"""

threadTemplate: """
  <div class="thread" _id="{{id}}">
    {{content}}
    <div class="comments">
    </div>
  </div>
"""

commentTemplate: """
  <div class="comment" _id="{{id}}">
    {{content}}
    <div class="comments">
    </div>
  </div>
"""

contentTemplate: """
  <div class="discussion-content"> 
    <div class="discussion-content-wrapper clearfix">
      {{vote}}
      <div class="discussion-right-wrapper clearfix">
        {{title}}
        <div class="discussion-content-view">
          <div class="content-body {{type}}-body" id="content-body-{{id}}">{{body}}</div>
          <div class="content-raw-body {{type}}-raw-body" style="display: none">{{body}}</div>
          {{tags}}
          {{bottom_bar}}
        </div>
      </div>
    </div>
  </div>
"""

tagsTemplate = """
  <div class="thread-tags">

  </div>
  <div class="thread-raw-tags" style="display: none">

"""
###

@Discussion = $.extend @Discussion,

###
  renderThread: (thread) ->
    rendered_title = Mustache.render titleTemplate, thread

    content_view =
      tags: rendered_tags
      rendered_bottom_bar: rendered_bottom_bar
      rendered_title: rendered_title
      rendered_vote: rendered_vote

    rendered_content = Mustache.render contentTemplate, $.extend(thread, contentView)
        
    Mustache.render threadTemplate, {rendered_content: rendered_content}

  renderComment: (comment) ->
  
    

  

  commentTemplate: """


  """
###


  newPostTemplate: """
    <form class="new-post-form" _id="{{discussion_id}}">
      <ul class="discussion-errors"></ul>    
      <input type="text" class="new-post-title title-input" placeholder="Title"/>
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
      <a class="discussion-submit-update control-button" href="javascript:void(0)">Update</a>
      <a class="discussion-cancel-update control-button" href="javascript:void(0)">Cancel</a>
    </form>
  """
