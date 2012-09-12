if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: ->
      @bind "add", (item) =>
        item.discussion = @
      @comparator = @sortByDateRecentFirst
      @on "thread:remove", (thread) =>
        @remove(thread)

    find: (id) ->
      _.first @where(id: id)

    addThread: (thread, options) ->
      options ||= {}
      model = new Thread thread
      @add model
      model

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
