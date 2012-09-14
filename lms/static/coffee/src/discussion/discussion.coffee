if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: (models, options={})->
      @pages = options['pages'] || 1
      @current_page = 1
      @bind "add", (item) =>
        item.discussion = @
      @comparator = @sortByDateRecentFirst
      @on "thread:remove", (thread) =>
        @remove(thread)

    find: (id) ->
      _.first @where(id: id)

    hasMorePages: ->
      @current_page < @pages

    addThread: (thread, options) ->
      # TODO: Check for existing thread with same ID in a faster way
      if not @find(thread.id)
        options ||= {}
        model = new Thread thread
        @add model
        model

    retrieveAnotherPage: (search_text="", commentable_ids="", sort_key="")->
      # TODO: I really feel that this belongs in DiscussionThreadListView
      @current_page += 1
      url = DiscussionUtil.urlFor 'threads'
      data = { page: @current_page }
      if search_text
        data['text'] = search_text
      if sort_key
        data['sort_key'] = sort_key
      if commentable_ids
        data['commentable_ids'] = commentable_ids
      DiscussionUtil.safeAjax
        $elem: @$el
        url: url
        data: data
        dataType: 'json'
        success: (response, textStatus) =>
          models = @models
          new_threads = [new Thread(data) for data in response.discussion_data][0]
          new_collection = _.union(models, new_threads)
          @reset new_collection

    sortByDate: (thread) ->
      thread.get("created_at")

    sortByDateRecentFirst: (thread) ->
      -(new Date(thread.get("created_at")).getTime())
      #return String.fromCharCode.apply(String,
      #  _.map(thread.get("created_at").split(""),
      #        ((c) -> return 0xffff - c.charChodeAt()))
      #)

    sortByVotes: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("votes")['up_count'])
      thread2_count = parseInt(thread2.get("votes")['up_count'])
      thread2_count - thread1_count

    sortByComments: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("comments_count"))
      thread2_count = parseInt(thread2.get("comments_count"))
      thread2_count - thread1_count
