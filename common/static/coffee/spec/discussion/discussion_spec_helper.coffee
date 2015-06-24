class @DiscussionSpecHelper
    # This is sad. We should avoid dependence on global vars.
    @setUpGlobals = ->
        DiscussionUtil.loadRoles({"Moderator": [], "Administrator": [], "Community TA": []})
        window.$$course_id = "edX/999/test"
        window.user = new DiscussionUser({username: "test_user", id: "567", upvoted_ids: []})
        DiscussionUtil.setUser(window.user)

    @makeTA = () ->
        DiscussionUtil.roleIds["Community TA"].push(parseInt(DiscussionUtil.getUser().id))

    @makeModerator = () ->
        DiscussionUtil.roleIds["Moderator"].push(parseInt(DiscussionUtil.getUser().id))

    @makeAjaxSpy = (fakeAjax) ->
        spyOn($, "ajax").andCallFake(
            (params) ->
                fakeAjax(params)
                {always: ->}
        )

    @makeEventSpy = () ->
        jasmine.createSpyObj('event', ['preventDefault', 'target'])

    @makeCourseSettings = (is_cohorted=true) ->
        new DiscussionCourseSettings(
            category_map:
                children: ['Test Topic', 'Other Topic']
                entries:
                    'Test Topic':
                        is_cohorted: is_cohorted
                        id: 'test_topic'
                    'Other Topic':
                        is_cohorted: is_cohorted
                        id: 'other_topic'
            is_cohorted: is_cohorted
        )

    @setUnderscoreFixtures = ->
        for templateName in ['thread-show']
            templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore')
            appendSetFixtures($('<script>', { id: templateName + '-template', type: 'text/template' })
                .text(templateFixture))
        appendSetFixtures("""
<div id="fixture-element"></div>

<!--
NOTE the html markup here comes from rendering lms/templates/discussion/_underscore_templates.html through a
browser and pasting the output.  When that file changes, this one should be regenerated alongside it.
-->
<script aria-hidden="true" type="text/template" id="thread-template">
    <article class="discussion-article" data-id="<%- id %>">
        <div class="thread-wrapper">
            <div class="forum-thread-main-wrapper">
                <div class="thread-content-wrapper"></div>
                <div class="post-extended-content">
                    <ol class="responses js-marked-answer-list"></ol>
                </div>
            </div>
            <div class="post-extended-content">
                <div class="response-count"/>
                <div class="add-response">
                    <button class="button add-response-btn">
                        <i class="icon fa fa-reply"></i>
                        <span class="add-response-btn-text">Add A Response</span>
                    </button>
                </div>
                <ol class="responses js-response-list"/>
                <div class="response-pagination"/>
                <div class="post-status-closed bottom-post-status" style="display: none">
                  This thread is closed.
                </div>
                <form class="discussion-reply-new" data-id="<%- id %>">
                    <h4>Post a response:</h4>
                    <ul class="discussion-errors"></ul>
                    <div class="reply-body" data-id="<%- id %>"></div>
                    <div class="reply-post-control">
                        <a class="discussion-submit-post control-button" href="#">Submit</a>
                    </div>
                </form>
            </div>
        </div>
        <div class="post-tools">
            <a href="javascript:void(0)" class="forum-thread-expand"><span class="icon fa fa-plus"/> Expand discussion</a>
            <a href="javascript:void(0)" class="forum-thread-collapse"><span class="icon fa fa-minus"/> Collapse discussion</a>
        </div>
    </article>
</script>

<script aria-hidden="true" type="text/template" id="thread-edit-template">
    <h1>Editing post</h1>
    <ul class="edit-post-form-errors"></ul>
    <div class="forum-edit-post-form-wrapper"></div>
    <div class="form-row">
      <label class="sr" for="edit-post-title">Edit post title</label>
      <input type="text" id="edit-post-title" class="edit-post-title" name="title" value="<%-title %>" placeholder="Title">
    </div>
    <div class="form-row">
      <div class="edit-post-body" name="body"><%- body %></div>
    </div>
    <input type="submit" id="edit-post-submit" class="post-update" value="Update post">
    <a href="#" class="post-cancel">Cancel</a>
</script>

<script aria-hidden="true" type="text/template" id="thread-response-template">
    <div class="discussion-response"></div>
    <a href="#" class="action-show-comments">
        <%- interpolate('Show Comments (%(num_comments)s)', {num_comments: comments.length}, true) %>
        <i class="icon fa fa-caret-down"></i>
    </a>
    <ol class="comments">
        <li class="new-comment">
            <form class="comment-form" data-id="<%- wmdId %>">
                <ul class="discussion-errors"></ul>
                <label class="sr" for="add-new-comment">Add a comment</label>
                <div class="comment-body" id="add-new-comment" data-id="<%- wmdId %>"
                data-placeholder="Add a comment..."></div>
                <div class="comment-post-control">
                    <a class="discussion-submit-comment control-button" href="#">Submit</a>
                </div>
            </form>
        </li>
    </ol>
</script>

<script aria-hidden="true" type="text/template" id="thread-response-show-template">
    <header>
      <div class="response-header-content">
        <%= author_display %>
        <p class="posted-details">
            <span class="timeago" title="<%= created_at %>"><%= created_at %></span>

              <% if (obj.endorsement) { %> - <%=
                interpolate(
                    thread.get("thread_type") == "question" ?
                      (endorsement.username ? "marked as answer %(time_ago)s by %(user)s" : "marked as answer %(time_ago)s") :
                      (endorsement.username ? "endorsed %(time_ago)s by %(user)s" : "endorsed %(time_ago)s"),
                    {
                        'time_ago': '<span class="timeago" title="' + endorsement.time + '">' + endorsement.time + '</span>',
                        'user': endorser_display
                    },
                    true
                )%><% } %>
          </p>
          <div class="post-labels">
              <span class="post-label-reported"><i class="icon fa fa-flag"></i>Reported</span>
          </div>
          </div>
          <div class="response-header-actions">
            <%=
                _.template(
                    $('#forum-actions').html(),
                    {
                        contentId: cid,
                        contentType: 'response',
                        primaryActions: ['vote', thread.get('thread_type') == 'question' ? 'answer' : 'endorse'],
                        secondaryActions: ['edit', 'delete', 'report']
                    }
                )
            %>
          </div>
    </header>

    <div class="response-body"><%- body %></div>
</script>

<script aria-hidden="true" type="text/template" id="thread-response-edit-template">
  <div class="edit-post-form">
    <h1>Editing response</h1>
    <ul class="edit-post-form-errors"></ul>
    <div class="form-row">
      <div class="edit-post-body" name="body" data-id="<%- id %>"><%- body %></div>
    </div>
    <input type="submit" id="edit-response-submit"class="post-update" value="Update response">
    <a href="#" class="post-cancel">Cancel</a>
  </div>
</script>

<script aria-hidden="true" type="text/template" id="response-comment-show-template">
  <div id="comment_<%- id %>">
    <div class="response-body"><%- body %></div>
    <%=
        _.template(
            $('#forum-actions').html(),
            {
                contentId: cid,
                contentType: 'comment',
                primaryActions: [],
                secondaryActions: ['edit', 'delete', 'report']
            }
        )
    %>

    <p class="posted-details">
    <%=
      interpolate(
        'posted %(time_ago)s by %(author)s',
        {'time_ago': '<span class="timeago" title="' + created_at + '">' + created_at + '</span>', 'author': author_display},
        true
      )%>
    </p>
    <div class="post-labels">
      <span class="post-label-reported"><i class="icon fa fa-flag"></i>Reported</span>
    </div>
  </div>
</script>

<script aria-hidden="true" type="text/template" id="response-comment-edit-template">
  <div class="edit-post-form" id="comment_<%- id %>">
    <h1>Editing comment</h1>
    <ul class="edit-comment-form-errors"></ul>
    <div class="form-row">
      <div class="edit-comment-body" name="body" data-id="<%- id %>"><%- body %></div>
    </div>
    <input type="submit" id="edit-comment-submit" class="post-update" value="Update comment">
    <a href="#" class="post-cancel">Cancel</a>
  </div>
</script>

<script aria-hidden="true" type="text/template" id="thread-list-item-template">
  <li data-id="<%- id %>" class="forum-nav-thread<% if (typeof(read) != "undefined" && !read) { %> is-unread<% } %>">
    <a href="#" class="forum-nav-thread-link">
      <div class="forum-nav-thread-wrapper-0">
        <%
        var icon_class, sr_text;
        if (thread_type == "discussion") {
            icon_class = "fa-comments";
            sr_text = "discussion";
        } else if (endorsed) {
            icon_class = "fa-check";
            sr_text = "answered question";
        } else {
            icon_class = "fa-question";
            sr_text = "unanswered question";
        }
        %>
        <span class="sr"><%= sr_text %></span>
        <i class="icon fa <%= icon_class %>"></i>
      </div><div class="forum-nav-thread-wrapper-1">
        <span class="forum-nav-thread-title"><%- title %></span>

        <%
        var labels = "";
        if (pinned) {
            labels += '<li class="post-label-pinned"><i class="icon fa fa-thumb-tack"></i>Pinned</li> ';
        }
        if (typeof(subscribed) != "undefined" && subscribed) {
            labels += '<li class="post-label-following"><i class="icon fa fa-star"></i>Following</li> ';
        }
        if (staff_authored) {
            labels += '<li class="post-label-by-staff"><i class="icon fa fa-user"></i>By: Staff</li> ';
        }
        if (community_ta_authored) {
            labels += '<li class="post-label-by-community-ta"><i class="icon fa fa-user"></i>By: Community TA</li> ';
        }
        if (labels != "") {
            print('<ul class="forum-nav-thread-labels">' + labels + '</ul>');
        }
        %>
      </div><div class="forum-nav-thread-wrapper-2">

        <span class="forum-nav-thread-votes-count">+<%=
            interpolate(
                '%(votes_up_count)s%(span_sr_open)s votes %(span_close)s',
                {'span_sr_open': '<span class="sr">', 'span_close': '</span>', 'votes_up_count': votes['up_count']},
                true
                )
        %></span>

        <span class="forum-nav-thread-comments-count <% if (unread_comments_count > 0) { %>is-unread<% } %>">
            <%
        var fmt;
        // Counts in data do not include the post itself, but the UI should
        var data = {
            'span_sr_open': '<span class="sr">',
            'span_close': '</span>',
            'unread_comments_count': unread_comments_count + (read ? 0 : 1),
            'comments_count': comments_count + 1
            };
        if (unread_comments_count > 0) {
            fmt = '%(comments_count)s %(span_sr_open)scomments (%(unread_comments_count)s unread comments)%(span_close)s';
        } else {
            fmt = '%(comments_count)s %(span_sr_open)scomments %(span_close)s';
        }
        print(interpolate(fmt, data, true));
        %>
        </span>
      </div>
    </a>
  </li>
</script>

<script aria-hidden="true" type="text/template" id="discussion-home">
  <div class="discussion-article blank-slate">
    <section class="home-header">
      <span class="label">DISCUSSION HOME:</span>
        <h1 class="home-title">Cohort Course</h1>
    </section>

     </div>
</script>

<script aria-hidden="true" type="text/template" id="search-alert-template">
    <div class="search-alert" id="search-alert-<%- cid %>">
        <div class="search-alert-content">
          <p class="message"><%= message %></p>
        </div>

        <div class="search-alert-controls">
          <a href="#" class="dismiss control control-dismiss"><i class="icon fa fa-remove"></i></a>
        </div>
    </div>
</script>

<script aria-hidden="true" type="text/template" id="new-post-template">
    <form class="forum-new-post-form">
        <ul class="post-errors" style="display: none"></ul>
        <div class="forum-new-post-form-wrapper"></div>
        <% if (cohort_options) { %>
        <div class="post-field group-selector-wrapper<% if (!is_commentable_cohorted) { %> disabled<% } %>">
            <label class="field-label">
                <span class="field-label-text">
                    Visible To:
                </span><select class="field-input js-group-select" name="group_id" <% if (!is_commentable_cohorted) { %>disabled<% } %>>
                    <option value="">All Groups</option>
                    <% _.each(cohort_options, function(opt) { %>
                    <option value="<%= opt.value %>" <% if (opt.selected) { %>selected<% } %>><%- opt.text %></option>
                    <% }); %>
                 </select>
            </label><div class="field-help">
                Discussion admins, moderators, and TAs can make their posts visible to all students or specify a single cohort.
            </div>
        </div>
        <% } %>
        <div class="post-field">
            <label class="field-label">
                <span class="sr">Title:</span>
                <input type="text" class="field-input js-post-title" name="title" placeholder="Title">
            </label><span class="field-help">
                Add a clear and descriptive title to encourage participation.
            </span>
        </div>
        <div class="post-field js-post-body editor" name="body" data-placeholder="Enter your question or comment"></div>
        <div class="post-options">
            <label class="post-option is-enabled">
                <input type="checkbox" name="follow" class="post-option-input js-follow" checked>
                <i class="icon fa fa-star"></i>follow this post
            </label>
            <% if (allow_anonymous) { %>
            <label class="post-option">
                <input type="checkbox" name="anonymous" class="post-option-input js-anon">
                post anonymously
            </label>
            <% } %>
            <% if (allow_anonymous_to_peers) { %>
            <label class="post-option">
                <input type="checkbox" name="anonymous_to_peers" class="post-option-input js-anon-peers">
                post anonymously to classmates
            </label>
            <% } %>
        </div>
        <div>
            <input type="submit" class="submit" value="Add Post">
            <a href="#" class="cancel">Cancel</a>
        </div>
    </form>
</script>

<script aria-hidden="true" type="text/template" id="thread-type-template">
    <div class="post-field">
        <div class="field-label">
            <span class="field-label-text">
                "Post type:"
            </span><fieldset class="field-input">
                <input type="radio" name="<%= form_id %>-post-type" class="post-type-input" id="<%= form_id %>-post-type-question" value="question" checked>
                <label for="<%= form_id %>-post-type-question" class="post-type-label">
                    <i class="icon fa fa-question"></i>
                    "Question"
                </label>
                <input type="radio" name="<%= form_id %>-post-type" class="post-type-input" id="<%= form_id %>-post-type-discussion" value="discussion">
                <label for="<%= form_id %>-post-type-discussion" class="post-type-label">
                    <i class="icon fa fa-comments"></i>
                    "Discussion"
                </label>
            </fieldset>
        </div><span class="field-help">
            "Questions raise issues that need answers. Discussions share ideas and start conversations."
        </span>
    </div>
</script>

<script aria-hidden="true" type="text/template" id="new-post-menu-entry-template">
    <li role="menuitem" class="topic-menu-item">
        <a href="#" class="topic-title" data-discussion-id="<%- id %>" data-cohorted="<%- is_cohorted %>"><%- text %></a>
    </li>
</script>

<script aria-hidden="true" type="text/template" id="new-post-menu-category-template">
    <li role="menuitem" class="topic-menu-item">
        <span class="topic-title"><%- text %></span>
        <ul role="menu" class="topic-submenu"><%= entries %></ul>
    </li>
</script>

<script aria-hidden="true" type="text/template" id="topic-template">
    <div class="field-label">
        <span class="field-label-text">Topic Area:</span><div class="field-input post-topic">
            <a href="#" class="post-topic-button">
                <span class="sr">Discussion topics; current selection is: </span>
                <span class="js-selected-topic"></span>
                <span class="drop-arrow" aria-hidden="true">▾</span>
            </a>
            <div class="topic-menu-wrapper">
                <label class="topic-filter-label">
                    <span class="sr">Filter topics</span>
                    <input type="text" class="topic-filter-input" placeholder="Filter topics">
                </label>
                <ul class="topic-menu" role="menu"><%= topics_html %></ul>
           </div>
       </div>
    </div><span class="field-help">
        Add your post to a relevant topic to help others find it.
    </span>
</script>




    <script type="text/template" id="forum-action-endorse">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-button action-endorse" role="checkbox" aria-checked="false">
                <span class="sr">Endorse</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Endorse</span>
                    <span class="label-checked">Unendorse</span>
                </span>
                <span class="action-icon"><i class="icon fa fa-check"></i></span>
            </a>
        </li>
    </script>


    <script type="text/template" id="forum-action-answer">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-button action-answer" role="checkbox" aria-checked="false">
                <span class="sr">Mark as Answer</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Mark as Answer</span>
                    <span class="label-checked">Unmark as Answer</span>
                </span>
                <span class="action-icon"><i class="icon fa fa-check"></i></span>
            </a>
        </li>
    </script>


    <script type="text/template" id="forum-action-follow">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-button action-follow" role="checkbox" aria-checked="false">
                <span class="sr">Follow</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Follow</span>
                    <span class="label-checked">Unfollow</span>
                </span>
                <span class="action-icon"><i class="icon fa fa-star"></i></span>
            </a>
        </li>
    </script>


<script type="text/template" id="forum-action-vote">
    <li class="actions-item">
        <span aria-hidden="true" class="display-vote" style="display: none;">
          <span class="vote-count"></span>
        </span>
        <a href="#" class="action-button action-vote" role="checkbox" aria-checked="false">
            <span class="sr">Vote</span>
            <span class="sr js-sr-vote-count"></span>

            <span class="action-label" aria-hidden="true">
              <span class="vote-count"></span>
            </span>

            <span class="action-icon" aria-hidden="true">
                <i class="icon fa fa-plus"></i>
            </span>
        </a>
    </li>
</script>




    <script type="text/template" id="forum-action-report">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-list-item action-report" role="checkbox" aria-checked="false">
                <span class="sr">Report abuse</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Report</span>
                    <span class="label-checked">Unreport</span>
                </span>
                <span class="action-icon">
                  <i class="icon fa fa-flag"></i>
                </span>
            </a>
        </li>
    </script>


    <script type="text/template" id="forum-action-pin">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-list-item action-pin" role="checkbox" aria-checked="false">
                <span class="sr">Pin</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Pin</span>
                    <span class="label-checked">Unpin</span>
                </span>
                <span class="action-icon">
                  <i class="icon fa fa-thumb-tack"></i>
                </span>
            </a>
        </li>
    </script>


    <script type="text/template" id="forum-action-close">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-list-item action-close" role="checkbox" aria-checked="false">
                <span class="sr">Close</span>
                <span class="action-label" aria-hidden="true">
                    <span class="label-unchecked">Close</span>
                    <span class="label-checked">Open</span>
                </span>
                <span class="action-icon">
                  <i class="icon fa fa-lock"></i>
                </span>
            </a>
        </li>
    </script>





    <script type="text/template" id="forum-action-edit">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-list-item action-edit" role="button">
                <span class="action-label">Edit</span>
                <span class="action-icon"><i class="icon fa fa-pencil"></i></span>
            </a>
        </li>
    </script>


    <script type="text/template" id="forum-action-delete">
        <li class="actions-item">
            <a href="javascript:void(0)" class="action-list-item action-delete" role="button">
                <span class="action-label">Delete</span>
                <span class="action-icon"><i class="icon fa fa-remove"></i></span>
            </a>
        </li>
    </script>


<script type="text/template" id="forum-actions">
    <ul class="<%= contentType %>-actions-list">
        <% _.each(primaryActions, function(action) { print(_.template($('#forum-action-' + action).html(), {})) }) %>
        <li class="actions-item is-visible">
            <div class="more-wrapper">
                <a href="javascript:void(0)" class="action-button action-more" role="button" aria-haspopup="true" aria-controls="action-menu-<%= contentId %>">
                    <span class="action-label">More</span>
                    <span class="action-icon"><i class="icon fa fa-ellipsis-h"></i></span>
                </a>
                <div class="actions-dropdown" id="action-menu-<%= contentType %>" aria-expanded="false">
                  <ul class="actions-dropdown-list">
                    <% _.each(secondaryActions, function(action) { print(_.template($('#forum-action-' + action).html(), {})) }) %>
                  </ul>
                </div>
            </div>
        </li>
    </ul>
</script>

<script aria-hidden="true" type="text/template" id="post-user-display-template">
    <% if (username) { %>
    <a href="<%- user_url %>" class="username"><%- username %></a>
        <% if (is_community_ta) { %>
        <span class="user-label-community-ta">Community TA</span>
        <% } else if (is_staff) { %>
        <span class="user-label-staff">Staff</span>
        <% } %>
    <% } else { %>
    anonymous
    <% } %>
</script>
""")
