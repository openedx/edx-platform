if Backbone?
  class @DiscussionThreadEditView  extends Backbone.View
    tagName: 'form',
    events:
      'submit': 'updateHandler',
      'click .post-cancel': 'cancelHandler'


    attributes:
      'class': 'discussion-post edit-post-form'

    initialize: (options) =>
      @container = options.container || $('.thread-content-wrapper')
      @mode = options.mode || 'inline'
      @course_settings = options.course_settings
      @threadType = @model.get('thread_type')
      @topicId = @model.get('commentable_id')
      _.bindAll(this)
      return this

    render: () =>
        formId = _.uniqueId("form-")
        @template = _.template($('#thread-edit-template').html())
        @$el.html(@template(@model.toJSON())).appendTo(@container)
        @submitBtn = @$('.post-update')
        threadTypeTemplate = _.template($("#thread-type-template").html())
        @addField(threadTypeTemplate({form_id: formId}))
        @$("#" + formId + "-post-type-" + @threadType).attr('checked', true)
        @topicView = new DiscussionTopicMenuView({
            topicId: @topicId,
            course_settings: @course_settings
        })
        @addField(@topicView.render())
        DiscussionUtil.makeWmdEditor(@$el, $.proxy(@$, this), 'edit-post-body')
        return this

    addField: (fieldView) =>
        @$('.forum-edit-post-form-wrapper').append(fieldView)
        return this

    isTabMode: () =>
      @mode == 'tab'

    save: () =>
        title = @$('.edit-post-title').val()
        threadType = @$(".post-type-input:checked").val()
        body = @$('.edit-post-body textarea').val()

        commentableId = @topicView.getCurrentTopicId()
        postData = {
            title: title,
            thread_type: threadType,
            body: body,
            commentable_id: commentableId
        }

        DiscussionUtil.safeAjax({
          $elem: @submitBtn,
          $loading: @submitBtn,
          url: DiscussionUtil.urlFor('update_thread', @model.id),
          type: 'POST',
          dataType: 'json',
          # TODO when the rest of the stuff below is made to work properly.
          # Note it can be forced to true on global basis via DiscussionUtils.force_async
          async: false,
          data: postData,
          error: DiscussionUtil.formErrorHandler(@$('.post-errors')),
          success: =>
            # @TODO: Move this out of the callback, this makes it feel sluggish
            @$('.edit-post-title').val('').attr('prev-text', '');
            @$('.edit-post-body textarea').val('').attr('prev-text', '');
            @$('.wmd-preview p').html('');
            postData.courseware_title = @topicView.getFullTopicName();
            @model.set(postData).unset('abbreviatedBody');
            @trigger('thread:updated');
            if (@threadType != threadType)
              @model.trigger('thread:thread_type_updated')
              @trigger('comment:endorse')
        })

    updateHandler: (event) =>
      event.preventDefault()
      # this event is for the moment triggered and used nowhere.
      @trigger('thread:update', event)
      @save()
      return this

    cancelHandler: (event) =>
      event.preventDefault()
      @trigger("thread:cancel_edit", event)
      @remove()
      return this
