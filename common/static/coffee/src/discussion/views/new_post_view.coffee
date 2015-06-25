if Backbone?
  class @NewPostView extends Backbone.View

      initialize: (options) ->
          @mode = options.mode or "inline"  # allowed values are "tab" or "inline"
          if @mode not in ["tab", "inline"]
              throw new Error("invalid mode: " + @mode)
          @course_settings = options.course_settings
          @is_commentable_cohorted = options.is_commentable_cohorted
          @topicId = options.topicId

      render: () ->
          context = _.clone(@course_settings.attributes)
          _.extend(context, {
              cohort_options: @getCohortOptions(),
              is_commentable_cohorted: @is_commentable_cohorted,
              mode: @mode,
              form_id: @mode + (if @topicId then "-" + @topicId else "")
          })
          @$el.html(_.template($("#new-post-template").html(), context))
          threadTypeTemplate = _.template($("#thread-type-template").html());
          if $('.js-group-select').is(':disabled')
              $('.group-selector-wrapper').addClass('disabled')
          @addField(threadTypeTemplate({form_id: _.uniqueId("form-")}));
          if @isTabMode()
              @topicView = new DiscussionTopicMenuView {
                  topicId:  @topicId
                  course_settings: @course_settings
              }
              @topicView.on('thread:topic_change', @toggleGroupDropdown)
              @addField(@topicView.render())
          DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "js-post-body"

      addField: (fieldView) ->
          @$('.forum-new-post-form-wrapper').append fieldView

      isTabMode: () ->
          @mode is "tab"

      getCohortOptions: () ->
          if @course_settings.get("is_cohorted") and DiscussionUtil.isPrivilegedUser()
              user_cohort_id = $("#discussion-container").data("user-cohort-id")
              _.map @course_settings.get("cohorts"), (cohort) ->
                  {value: cohort.id, text: cohort.name, selected: cohort.id==user_cohort_id}
          else
              null

      events:
          "submit .forum-new-post-form": "createPost"
          "change .post-option-input": "postOptionChange"
          "click .cancel": "cancel"
          "reset .forum-new-post-form": "updateStyles"

      toggleGroupDropdown: ($target) ->
        if $target.data('cohorted')
            $('.js-group-select').prop('disabled', false);
            $('.group-selector-wrapper').removeClass('disabled')
        else
            $('.js-group-select').val('').prop('disabled', true);
            $('.group-selector-wrapper').addClass('disabled')

      postOptionChange: (event) ->
          $target = $(event.target)
          $optionElem = $target.closest(".post-option")
          if $target.is(":checked")
              $optionElem.addClass("is-enabled")
          else
              $optionElem.removeClass("is-enabled")

      createPost: (event) ->
          event.preventDefault()
          thread_type = @$(".post-type-input:checked").val()
          title   = @$(".js-post-title").val()
          body    = @$(".js-post-body").find(".wmd-input").val()
          group   = @$(".js-group-select option:selected").attr("value")

          anonymous          = false || @$(".js-anon").is(":checked")
          anonymous_to_peers = false || @$(".js-anon-peers").is(":checked")
          follow             = false || @$(".js-follow").is(":checked")

          topicId = if @isTabMode() then @topicView.getCurrentTopicId() else @topicId
          url = DiscussionUtil.urlFor('create_thread', topicId)

          DiscussionUtil.safeAjax
              $elem: $(event.target)
              $loading: $(event.target) if event
              url: url
              type: "POST"
              dataType: 'json'
              async: false # TODO when the rest of the stuff below is made to work properly..
              data:
                  thread_type: thread_type
                  title: title
                  body: body
                  anonymous: anonymous
                  anonymous_to_peers: anonymous_to_peers
                  auto_subscribe: follow
                  group_id: group
              error: DiscussionUtil.formErrorHandler(@$(".post-errors"))
              success: (response, textStatus) =>
                  # TODO: Move this out of the callback, this makes it feel sluggish
                  thread = new Thread response['content']
                  @$el.hide()
                  @resetForm()
                  @collection.add thread

      cancel: (event) ->
        event.preventDefault()
        if not confirm gettext("Your post will be discarded.")
          return
        @trigger('newPost:cancel')
        @resetForm()

      resetForm: =>
        @$(".forum-new-post-form")[0].reset()
        DiscussionUtil.clearFormErrors(@$(".post-errors"))
        @$(".wmd-preview p").html("")
        if @isTabMode()
          @topicView.setTopic(@$("a.topic-title").first())

      updateStyles: =>
        # form reset doesn't change the style of checkboxes so this event is to do that job
        setTimeout(
          (=> @$(".post-option-input").trigger("change")),
          1
        )
