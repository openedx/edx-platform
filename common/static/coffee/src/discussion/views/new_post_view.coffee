if Backbone?
  class @NewPostView extends Backbone.View

      initialize: (options) ->
          @mode = options.mode or "inline"  # allowed values are "tab" or "inline"
          if @mode not in ["tab", "inline"]
              throw new Error("invalid mode: " + @mode)
          @course_settings = options.course_settings
          @maxNameWidth = 100
          @topicId = options.topicId

      render: () ->
          context = _.clone(@course_settings.attributes)
          _.extend(context, {
              cohort_options: @getCohortOptions(),
              mode: @mode,
              form_id: @mode + (if @topicId then "-" + @topicId else "")
          })
          context.topics_html = @renderCategoryMap(@course_settings.get("category_map")) if @mode is "tab"
          @$el.html(_.template($("#new-post-template").html(), context))

          if @mode is "tab"
              # set up the topic dropdown in tab mode
              @dropdownButton = @$(".post-topic-button")
              @topicMenu      = @$(".topic-menu-wrapper")
              @hideTopicDropdown()
              @setTopic(@$("a.topic-title").first())

          DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "js-post-body"

      renderCategoryMap: (map) ->
          category_template = _.template($("#new-post-menu-category-template").html())
          entry_template = _.template($("#new-post-menu-entry-template").html())
          html = ""
          for name in map.children
              if name of map.entries
                  entry = map.entries[name]
                  html += entry_template({text: name, id: entry.id, is_cohorted: entry.is_cohorted})
              else # subcategory
                  html += category_template({text: name, entries: @renderCategoryMap(map.subcategories[name])})
          html

      getCohortOptions: () ->
          if @course_settings.get("is_cohorted") and DiscussionUtil.isPrivilegedUser()
              user_cohort_id = $("#discussion-container").data("user-cohort-id")
              _.map @course_settings.get("cohorts"), (cohort) ->
                  {value: cohort.id, text: cohort.name, selected: cohort.id==user_cohort_id}
          else
              null

      events:
          "submit .forum-new-post-form": "createPost"
          "click .post-topic-button": "toggleTopicDropdown"
          "click .topic-menu-wrapper": "handleTopicEvent"
          "click .topic-filter-label": "ignoreClick"
          "keyup .topic-filter-input": DiscussionFilter.filterDrop
          "change .post-option-input": "postOptionChange"
          "click .cancel": "cancel"
          "reset .forum-new-post-form": "updateStyles"

      # Because we want the behavior that when the body is clicked the menu is
      # closed, we need to ignore clicks in the search field and stop propagation.
      # Without this, clicking the search field would also close the menu.
      ignoreClick: (event) ->
          event.stopPropagation()

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
          group = @$(".js-group-select option:selected").attr("value")

          anonymous          = false || @$(".js-anon").is(":checked")
          anonymous_to_peers = false || @$(".js-anon-peers").is(":checked")
          follow             = false || @$(".js-follow").is(":checked")

          url = DiscussionUtil.urlFor('create_thread', @topicId)

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


      toggleTopicDropdown: (event) ->
          event.preventDefault()
          event.stopPropagation()
          if @menuOpen
              @hideTopicDropdown()
          else
              @showTopicDropdown()

      showTopicDropdown: () ->
          @menuOpen = true
          @dropdownButton.addClass('dropped')
          @topicMenu.show()
          $(".form-topic-drop-search-input").focus()

          $("body").bind "click", @hideTopicDropdown

          # Set here because 1) the window might get resized and things could
          # change and 2) can't set in initialize because the button is hidden
          @maxNameWidth = @dropdownButton.width() - 40

      # Need a fat arrow because hideTopicDropdown is passed as a callback to bind
      hideTopicDropdown: () =>
          @menuOpen = false
          @dropdownButton.removeClass('dropped')
          @topicMenu.hide()

          $("body").unbind "click", @hideTopicDropdown

      handleTopicEvent: (event) ->
          event.preventDefault()
          event.stopPropagation()
          @setTopic($(event.target))

      setTopic: ($target) ->
          if $target.data('discussion-id')
              @topicText = $target.html()
              @topicText  = @getFullTopicName($target)
              @topicId   = $target.data('discussion-id')
              @setSelectedTopic()
              if $target.data("cohorted")
                $(".js-group-select").prop("disabled", false)
              else
                $(".js-group-select").val("")
                $(".js-group-select").prop("disabled", true)
              @hideTopicDropdown()

      setSelectedTopic: ->
          @$(".js-selected-topic").html(@fitName(@topicText))

      getFullTopicName: (topicElement) ->
          name = topicElement.html()
          topicElement.parents('.topic-submenu').each ->
              name = $(this).siblings('.topic-title').text() + ' / ' + name
          return name

      getNameWidth: (name) ->
          test = $("<div>")
          test.css
              "font-size": @dropdownButton.css('font-size')
              opacity: 0
              position: 'absolute'
              left: -1000
              top: -1000
          $("body").append(test)
          test.html(name)
          width = test.width()
          test.remove()
          return width

      fitName: (name) ->
          width = @getNameWidth(name)
          if width < @maxNameWidth
              return name
          path = (x.replace /^\s+|\s+$/g, "" for x in name.split("/"))
          while path.length > 1
              path.shift()
              partialName = gettext("…") + " / " + path.join(" / ")
              if  @getNameWidth(partialName) < @maxNameWidth
                  return partialName

          rawName = path[0]

          name = gettext("…") + " / " + rawName

          while @getNameWidth(name) > @maxNameWidth
              rawName = rawName[0...rawName.length-1]
              name =  gettext("…") + " / " + rawName + " " + gettext("…")

          return name

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
        if @mode is "tab"
          @setTopic(@$("a.topic-title").first())

      updateStyles: =>
        # form reset doesn't change the style of checkboxes so this event is to do that job
        setTimeout(
          (=> @$(".post-option-input").trigger("change")),
          1
        )
