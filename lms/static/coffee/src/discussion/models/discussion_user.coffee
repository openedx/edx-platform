class @DiscussionUser
    constructor: (content_info) ->
        @content_info = content_info

    following: (thread) ->
        @content_info[thread.id]['subscribed'] == true

    voted: (thread) ->
        @content_info[thread.id]['voted'] == 'up'

