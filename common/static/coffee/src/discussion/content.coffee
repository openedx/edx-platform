if Backbone?
  class @Content extends Backbone.Model

    @contents: {}
    @contentInfos: {}

    template: -> DiscussionUtil.getTemplate('_content')

    actions:
      editable: '.admin-edit'
      can_reply: '.discussion-reply'
      can_delete: '.admin-delete'
      can_openclose: '.admin-openclose'

    urlMappers: {}

    urlFor: (name) ->
      @urlMappers[name].apply(@)

    can: (action) ->
      (@get('ability') || {})[action]

    # Default implementation
    canBeEndorsed: -> false

    updateInfo: (info) ->
      if info
        @set('ability', info.ability)
        @set('voted', info.voted)
        @set('subscribed', info.subscribed)

    addComment: (comment, options) ->
      options ||= {}
      if not options.silent
        thread = @get('thread')
        comments_count = parseInt(thread.get('comments_count'))
        thread.set('comments_count', comments_count + 1)
      @get('children').push comment
      model = new Comment $.extend {}, comment, { thread: @get('thread') }
      @get('comments').add model
      @trigger "comment:add"
      model

    removeComment: (comment) ->
      thread = @get('thread')
      comments_count = parseInt(thread.get('comments_count'))
      thread.set('comments_count', comments_count - 1 - comment.getCommentsCount())
      @trigger "comment:remove"

    resetComments: (children) ->
      @set 'children', []
      @set 'comments', new Comments()
      for comment in (children || [])
        @addComment comment, { silent: true }

    initialize: ->
      Content.addContent @id, @
      userId = @get('user_id')
      if userId?
        @set('staff_authored', DiscussionUtil.isStaff(userId))
        @set('community_ta_authored', DiscussionUtil.isTA(userId))
      else
        @set('staff_authored', false)
        @set('community_ta_authored', false)
      if Content.getInfo(@id)
        @updateInfo(Content.getInfo(@id))
      @set 'user_url', DiscussionUtil.urlFor('user_profile', userId)
      @resetComments(@get('children'))

    remove: ->

      if @get('type') == 'comment'
        @get('thread').removeComment(@)
        @get('thread').trigger "comment:remove", @
      else
        @trigger "thread:remove", @

    @addContent: (id, content) -> @contents[id] = content

    @getContent: (id) -> @contents[id]

    @getInfo: (id) ->
      @contentInfos[id]

    @loadContentInfos: (infos) ->
      for id, info of infos
        if @getContent(id)
          @getContent(id).updateInfo(info)
      $.extend @contentInfos, infos

    pinThread: ->
      pinned = @get("pinned")
      @set("pinned",pinned)
      @trigger "change", @

    unPinThread: ->
      pinned = @get("pinned")
      @set("pinned",pinned)
      @trigger "change", @
    
    flagAbuse: ->
      temp_array = @get("abuse_flaggers")
      temp_array.push(window.user.get('id'))
      @set("abuse_flaggers",temp_array)
      @trigger "change", @

    unflagAbuse: ->
      @get("abuse_flaggers").pop(window.user.get('id'))
      @trigger "change", @

    isFlagged: ->
      user = DiscussionUtil.getUser()
      flaggers = @get("abuse_flaggers")
      user and (user.id in flaggers or (DiscussionUtil.isPrivilegedUser(user.id) and flaggers.length > 0))

    incrementVote: (increment) ->
      newVotes = _.clone(@get("votes"))
      newVotes.up_count = newVotes.up_count + increment
      @set("votes", newVotes)

    vote: ->
      @incrementVote(1)

    unvote: ->
      @incrementVote(-1)
    
  class @Thread extends @Content
    urlMappers:
      'retrieve'    : -> DiscussionUtil.urlFor('retrieve_single_thread', @.get('commentable_id'), @id)
      'reply'       : -> DiscussionUtil.urlFor('create_comment', @id)
      'unvote'      : -> DiscussionUtil.urlFor("undo_vote_for_#{@get('type')}", @id)
      'upvote'      : -> DiscussionUtil.urlFor("upvote_#{@get('type')}", @id)
      'downvote'    : -> DiscussionUtil.urlFor("downvote_#{@get('type')}", @id)
      'close'       : -> DiscussionUtil.urlFor('openclose_thread', @id)
      'update'      : -> DiscussionUtil.urlFor('update_thread', @id)
      '_delete'      : -> DiscussionUtil.urlFor('delete_thread', @id)
      'follow'      : -> DiscussionUtil.urlFor('follow_thread', @id)
      'unfollow'    : -> DiscussionUtil.urlFor('unfollow_thread', @id)
      'flagAbuse'   : -> DiscussionUtil.urlFor("flagAbuse_#{@get('type')}", @id)
      'unFlagAbuse' : -> DiscussionUtil.urlFor("unFlagAbuse_#{@get('type')}", @id)
      'pinThread'   : -> DiscussionUtil.urlFor("pin_thread", @id)
      'unPinThread' : -> DiscussionUtil.urlFor("un_pin_thread", @id)

    initialize: ->
      @set('thread', @)
      super()

    comment: ->
      @set("comments_count", parseInt(@get("comments_count")) + 1)

    follow: ->
      @set('subscribed', true)

    unfollow: ->
      @set('subscribed', false)

    display_body: ->
      if @has("highlighted_body")
        String(@get("highlighted_body")).replace(/<highlight>/g, '<mark>').replace(/<\/highlight>/g, '</mark>')
      else
        @get("body")

    display_title: ->
      if @has("highlighted_title")
        String(@get("highlighted_title")).replace(/<highlight>/g, '<mark>').replace(/<\/highlight>/g, '</mark>')
      else
        @get("title")

    toJSON: ->
      json_attributes = _.clone(@attributes)
      _.extend(json_attributes, { title: @display_title(), body: @display_body() })

    created_at_date: ->
      new Date(@get("created_at"))

    created_at_time: ->
      new Date(@get("created_at")).getTime()

    hasResponses: ->
      @get('comments_count') > 0

  class @Comment extends @Content
    urlMappers:
      'reply': -> DiscussionUtil.urlFor('create_sub_comment', @id)
      'unvote': -> DiscussionUtil.urlFor("undo_vote_for_#{@get('type')}", @id)
      'upvote': -> DiscussionUtil.urlFor("upvote_#{@get('type')}", @id)
      'downvote': -> DiscussionUtil.urlFor("downvote_#{@get('type')}", @id)
      'endorse': -> DiscussionUtil.urlFor('endorse_comment', @id)
      'update': -> DiscussionUtil.urlFor('update_comment', @id)
      '_delete': -> DiscussionUtil.urlFor('delete_comment', @id)
      'flagAbuse'   : -> DiscussionUtil.urlFor("flagAbuse_#{@get('type')}", @id)
      'unFlagAbuse' : -> DiscussionUtil.urlFor("unFlagAbuse_#{@get('type')}", @id)

    getCommentsCount: ->
      count = 0
      @get('comments').each (comment) ->
        count += comment.getCommentsCount() + 1
      count

    canBeEndorsed: =>
      user_id = window.user.get("id")
      user_id && (
        DiscussionUtil.isPrivilegedUser(user_id) ||
        (@get('thread').get('thread_type') == 'question' && @get('thread').get('user_id') == user_id)
      )

  class @Comments extends Backbone.Collection

    model: Comment

    initialize: ->
      @bind "add", (item) =>
        item.collection = @

    find: (id) ->
      _.first @where(id: id)
