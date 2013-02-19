if Backbone?
  class @DiscussionUser extends Backbone.Model
      following: (thread) ->
          _.include(@get('subscribed_thread_ids'), thread.id)

      voted: (thread) ->
          _.include(@get('upvoted_ids'), thread.id)

      vote: (thread) ->
          @get('upvoted_ids').push(thread.id)
          thread.vote()

      unvote: (thread) ->
          @set('upvoted_ids', _.without(@get('upvoted_ids'), thread.id))
          thread.unvote()
