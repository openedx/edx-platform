if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: (models, options={})->
      @pages = options['pages'] || 1
      @current_page = 1
      @sort_preference = options['sort']
      @bind "add", (item) =>
        item.discussion = @
      @setSortComparator(@sort_preference)
      @on "thread:remove", (thread) =>
        @remove(thread)

    find: (id) ->
      _.first @where(id: id)

    hasMorePages: ->
      @current_page < @pages

    setSortComparator: (sortBy) ->
      switch sortBy
        when 'date' then @comparator = @sortByDateRecentFirst
        when 'votes' then @comparator = @sortByVotes
        when 'comments' then @comparator = @sortByComments

    addThread: (thread, options) ->
      # TODO: Check for existing thread with same ID in a faster way
      if not @find(thread.id)
        options ||= {}
        model = new Thread thread
        @add model
        model

    retrieveAnotherPage: (mode, options={}, sort_options={}, error=null)->
      data = { page: @current_page + 1 }
      if _.contains(["unread", "unanswered", "flagged"], options.filter)
        data[options.filter] = true
      switch mode
        when 'search'
          url = DiscussionUtil.urlFor 'search'
          data['text'] = options.search_text
        when 'commentables'
          url = DiscussionUtil.urlFor 'search'
          data['commentable_ids'] = options.commentable_ids
        when 'all'
          url = DiscussionUtil.urlFor 'threads'
        when 'followed'
          url = DiscussionUtil.urlFor 'followed_threads', options.user_id
      if options['group_id']
        data['group_id'] = options['group_id']
      data['sort_key'] = sort_options.sort_key || 'date'
      data['sort_order'] = sort_options.sort_order || 'desc'
      DiscussionUtil.safeAjax
        $elem: @$el
        url: url
        data: data
        dataType: 'json'
        success: (response, textStatus) =>
          models = @models
          new_threads = [new Thread(data) for data in response.discussion_data][0]
          new_collection = _.union(models, new_threads)
          Content.loadContentInfos(response.annotated_content_info)
          @pages = response.num_pages
          @current_page = response.page
          @reset new_collection
        error: error

    sortByDate: (thread) ->
      #
      # The comment client asks each thread for a value by which to sort the collection
      # and calls this sort routine regardless of the order returned from the LMS/comments service
      # so, this takes advantage of this per-thread value and returns tomorrow's date
      # for pinned threads, ensuring that they appear first, (which is the intent of pinned threads)
      #
      @pinnedThreadsSortComparatorWithDate(thread, true)


    sortByDateRecentFirst: (thread) ->
      #
      # Same as above
      # but negative to flip the order (newest first)
      #
      @pinnedThreadsSortComparatorWithDate(thread, false)
      #return String.fromCharCode.apply(String,
      #  _.map(thread.get("created_at").split(""),
      #        ((c) -> return 0xffff - c.charChodeAt()))
      #)

    sortByVotes: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("votes")['up_count'])
      thread2_count = parseInt(thread2.get("votes")['up_count'])
      @pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count)

    sortByComments: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("comments_count"))
      thread2_count = parseInt(thread2.get("comments_count"))
      @pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count)

    pinnedThreadsSortComparatorWithCount: (thread1, thread2, thread1_count, thread2_count) ->
      # if threads are pinned they should be displayed on top.
      # Unpinned will be sorted by their property count
      if thread1.get('pinned') and not thread2.get('pinned')
        -1
      else if thread2.get('pinned') and not thread1.get('pinned')
        1
      else
        if thread1_count > thread2_count
          -1
        else if thread2_count > thread1_count
          1
        else
          if thread1.created_at_time() > thread2.created_at_time()
            -1
          else
            1

    pinnedThreadsSortComparatorWithDate: (thread, ascending)->
      # if threads are pinned they should be displayed on top.
      # Unpinned will be sorted by their date
      threadCreatedTime = new Date(thread.get("created_at")).getTime()
      if thread.get('pinned')
        #use tomorrow's date
        today = new Date();
        preferredDate = new Date(today.getTime() + (24 * 60 * 60 * 1000) + threadCreatedTime);
      else
        preferredDate = threadCreatedTime
      if ascending
        preferredDate
      else
        -(preferredDate)
