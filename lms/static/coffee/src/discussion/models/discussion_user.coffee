class @DiscussionUser extends Backbone.Model
    following: (thread) ->
        _.include(@get('subscribed_thread_ids'), thread.id)

    voted: (thread) ->
        _.include(@get('upvoted_ids'), thread.id)
