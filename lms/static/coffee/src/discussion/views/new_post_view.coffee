class @NewPostView extends Backbone.View

    initialize: () ->
        @dropdownButton = @$(".topic_dropdown_button")

    #events:
    #    "submit .new-post-form":            "createPost"
    #    "click  .topic_dropdown_button":    "toggleTopicDropdown"
    #    "click  .topic_menu":               "setTopic"

    #toggleTopicDropdown: (event) ->
    #    if $target.hasClass('dropped')
    #        @showTopicDropdown()
    #    else
    #        @hideTopicDropdown()
    #
    #showTopicDropdown: () ->
    #    #$button = 
    #    $button.addClass('dropped')

    #    $topicMenu = @$(".topic_menu")
    #    $topicMenu.show()

    #createPost: (event) ->
    #    event.preventDefault()

    #    title   = @$(".new-post-title").val()
    #    body    = @$(".new-post-body").val()
    #    tags    = @$(".new-post-tags").val()

    #    anonymous = false || @$("input.discussion-anonymous").is(":checked")
    #    follow    = false || @$("input.discussion-follow").is(":checked")

    #    $formTopicDropBtn.bind('click', showFormTopicDrop);
    #    $formTopicDropMenu.bind('click', setFormTopic);

    #    url = DiscussionUtil.urlFor('create_thread', @model.id)

    #    DiscussionUtil.safeAjax
    #        $elem: $(event.target)
    #        $loading: $(event.target) if event
    #        url: url
    #        type: "POST"
    #        dataType: 'json'
    #        data:
    #            title: title
    #            body: body
    #            tags: tags
    #            anonymous: anonymous
    #            auto_subscribe: follow
    #        error: DiscussionUtil.formErrorHandler(@$(".new-post-form-errors"))
    #        success: (response, textStatus) =>
    #            DiscussionUtil.clearFormErrors(@$(".new-post-form-errors"))
    #            $thread = $(response.html)
    #            @$el.children(".threads").prepend($thread)

    #            @$el.children(".blank").remove()

    #            @$(".new-post-similar-posts").empty()
    #            @$(".new-post-similar-posts-wrapper").hide()
    #            @$(".new-post-title").val("").attr("prev-text", "")
    #            DiscussionUtil.setWmdContent @$el, $.proxy(@$, @), "new-post-body", ""
    #            @$(".new-post-tags").val("")
    #            @$(".new-post-tags").importTags("")

    #            thread = @model.addThread response.content
    #            threadView = new ThreadView el: $thread[0], model: thread
    #            thread.updateInfo response.annotated_content_info
    #            @cancelNewPost()
