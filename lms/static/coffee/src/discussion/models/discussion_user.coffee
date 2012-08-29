class @DiscussionUser
    constructor: (content_info) ->
        @content_info = content_info

    following: (thread) ->
        _.include(@content_info['subscribed_thread_ids'], thread.id)

    voted: (thread) ->
        _.include(@content_info['upvoted_ids'], thread.id)
