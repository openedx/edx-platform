if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: (models, options={})->
      @pages = options['pages'] || 1
      @current_page = 1
      @slugToId = {}
      @bind "add", (item) =>
        item.discussion = @
        @updateSlugMap(item)
      @comparator = @sortByDateRecentFirst
      @on "thread:remove", (thread) =>
        @remove(thread)

      _.each models, @updateSlugMap
      @bind "reset", @onReset

    onReset: (new_collection)=>
      new_collection.each @updateSlugMap

    updateSlugMap: (thread)=>
      # Don't try to update if thread doesn't have slug
      # Thread could either be a raw JSON object or a Thread model...
      if not(thread.slug) and not (thread.get and thread.get('slug'))
        return
      slug = thread.slug or thread.get('slug')
      @slugToId[slug] = thread.id

    getBySlug: (slug) =>
      @get(@slugToId[slug])

    find: (id) ->
      _.first @where(id: id)

    hasMorePages: ->
      @current_page < @pages

    addThread: (thread, options) ->
      if not @get(thread.id)
        options ||= {}
        model = new Thread thread
        @add model
        model

    retrieveAnotherPage: (mode, options={}, sort_options={})->
      @current_page += 1
      data = { page: @current_page }
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
      data['sort_key'] = sort_options.sort_key || 'date'
      data['sort_order'] = sort_options.sort_order || 'desc'
      DiscussionUtil.safeAjax
        $elem: @$el
        url: url
        data: data
        dataType: 'json'
        success: (response, textStatus) =>
          models = @models
          new_threads = [new Thread(data) for data in response.threads][0]
          new_collection = _.union(models, new_threads)
          Content.loadContentInfos(response.annotated_content_info)
          @reset new_collection
          @pages = response.num_pages
          @current_page = response.page

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
      if thread2_count != thread1_count
        thread2_count - thread1_count
      else
        thread2.created_at_time() - thread1.created_at_time()

    sortByComments: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("comments_count"))
      thread2_count = parseInt(thread2.get("comments_count"))
      if thread2_count != thread1_count
        thread2_count - thread1_count
      else
        thread2.created_at_time() - thread1.created_at_time()
