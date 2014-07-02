if Backbone?
  class @NewPostView extends Backbone.View

      initialize: (options) ->
          @mode = options.mode or "inline"  # allowed values are "tab" or "inline"
          if @mode not in ["tab", "inline"]
              throw new Error("invalid mode: " + @mode)
          @course_settings = options.course_settings
          @maxNameWidth = 100

      render: () ->
          if @mode is "tab"
              @$el.html(
                  _.template(
                      $("#new-post-tab-template").html(), {
                          topic_dropdown_html: @getTopicDropdownHTML(),
                          options_html: @getOptionsHTML(),
                          editor_html: @getEditorHTML()
                      }
                  )
              )
              # set up the topic dropdown in tab mode
              @dropdownButton = @$(".topic_dropdown_button")
              @topicMenu      = @$(".topic_menu_wrapper")
              @menuOpen = @dropdownButton.hasClass('dropped')
              @topicId    = @$(".topic").first().data("discussion_id")
              @topicText  = @getFullTopicName(@$(".topic").first())
              $('.choose-cohort').hide() unless @$(".topic_menu li a").first().is("[cohorted=true]")
              @setSelectedTopic()
          else # inline
              @$el.html(
                  _.template(
                      $("#new-post-inline-template").html(), {
                          options_html: @getOptionsHTML(),
                          editor_html: @getEditorHTML()
                      }
                  )
              )
          DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "new-post-body"

      getTopicDropdownHTML: () ->
          # populate the category menu (topic dropdown)
          _renderCategoryMap = (map) ->
              category_template = _.template($("#new-post-menu-category-template").html())
              entry_template = _.template($("#new-post-menu-entry-template").html())
              html = ""
              for name in map.children
                  if name of map.entries
                      entry = map.entries[name]
                      html += entry_template({text: name, id: entry.id, is_cohorted: entry.is_cohorted})
                  else # subcategory
                      html += category_template({text: name, entries: _renderCategoryMap(map.subcategories[name])})
              html
          topics_html = _renderCategoryMap(@course_settings.get("category_map"))
          _.template($("#new-post-topic-dropdown-template").html(), {topics_html: topics_html})

      getEditorHTML: () ->
          _.template($("#new-post-editor-template").html(), {})

      getOptionsHTML: () ->
          # cohort options?
          if @course_settings.get("is_cohorted") and DiscussionUtil.isStaff()
              user_cohort_id = $("#discussion-container").data("user-cohort-id")
              cohort_options = _.map @course_settings.get("cohorts"), (cohort) ->
                  {value: cohort.id, text: cohort.name, selected: cohort.id==user_cohort_id}
          else
              cohort_options = null
          context = _.clone(@course_settings.attributes)
          context.cohort_options = cohort_options
          _.template($("#new-post-options-template").html(), context)

      events:
          "submit .new-post-form":            "createPost"
          "click  .topic_dropdown_button":    "toggleTopicDropdown"
          "click  .topic_menu_wrapper":       "setTopic"
          "click  .topic_menu_search":        "ignoreClick"
          "keyup .form-topic-drop-search-input": DiscussionFilter.filterDrop

      # Because we want the behavior that when the body is clicked the menu is
      # closed, we need to ignore clicks in the search field and stop propagation.
      # Without this, clicking the search field would also close the menu.
      ignoreClick: (event) ->
          event.stopPropagation()

      createPost: (event) ->
          event.preventDefault()
          title   = @$(".new-post-title").val()
          body    = @$(".new-post-body").find(".wmd-input").val()
          group = @$(".new-post-group option:selected").attr("value")

          anonymous          = false || @$("input.discussion-anonymous").is(":checked")
          anonymous_to_peers = false || @$("input.discussion-anonymous-to-peers").is(":checked")
          follow             = false || @$("input.discussion-follow").is(":checked")

          url = DiscussionUtil.urlFor('create_thread', @topicId)

          DiscussionUtil.safeAjax
              $elem: $(event.target)
              $loading: $(event.target) if event
              url: url
              type: "POST"
              dataType: 'json'
              async: false # TODO when the rest of the stuff below is made to work properly..
              data:
                  title: title
                  body: body
                  anonymous: anonymous
                  anonymous_to_peers: anonymous_to_peers
                  auto_subscribe: follow
                  group_id: group
              error: DiscussionUtil.formErrorHandler(@$(".new-post-form-errors"))
              success: (response, textStatus) =>
                  # TODO: Move this out of the callback, this makes it feel sluggish
                  thread = new Thread response['content']
                  DiscussionUtil.clearFormErrors(@$(".new-post-form-errors"))
                  @$el.hide()
                  @$(".new-post-title").val("").attr("prev-text", "")
                  @$(".new-post-body textarea").val("").attr("prev-text", "")
                  @$(".wmd-preview p").html("") # only line not duplicated in new post inline view
                  @collection.add thread

      toggleTopicDropdown: (event) ->
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

          $("body").bind "keydown", @setActiveItem
          $("body").bind "click", @hideTopicDropdown

          # Set here because 1) the window might get resized and things could
          # change and 2) can't set in initialize because the button is hidden
          @maxNameWidth = @dropdownButton.width() - 40

      # Need a fat arrow because hideTopicDropdown is passed as a callback to bind
      hideTopicDropdown: () =>
          @menuOpen = false
          @dropdownButton.removeClass('dropped')
          @topicMenu.hide()

          $("body").unbind "keydown", @setActiveItem
          $("body").unbind "click", @hideTopicDropdown

      setTopic: (event) ->
          $target = $(event.target)
          if $target.data('discussion_id')
              @topicText = $target.html()
              @topicText  = @getFullTopicName($target)
              @topicId   = $target.data('discussion_id')
              @setSelectedTopic()
              if $target.is('[cohorted=true]')
                $('.choose-cohort').show();
              else
                $('.choose-cohort').hide();

      setSelectedTopic: ->
          @dropdownButton.html(@fitName(@topicText) + ' <span class="drop-arrow">▾</span>')

      getFullTopicName: (topicElement) ->
          name = topicElement.html()
          topicElement.parents('ul').not('.topic_menu').each ->
              name = $(this).siblings('a').text() + ' / ' + name
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

      setActiveItem: (event) ->
          if event.which == 13
            $(".topic_menu_wrapper .focused").click()
            return
          if event.which != 40 && event.which != 38
            return
          event.preventDefault()

          items = $.makeArray($(".topic_menu_wrapper a").not(".hidden"))
          index = items.indexOf($('.topic_menu_wrapper .focused')[0])

          if event.which == 40
              index = Math.min(index + 1, items.length - 1)
          if event.which == 38
              index = Math.max(index - 1, 0)

          $(".topic_menu_wrapper .focused").removeClass("focused")
          $(items[index]).addClass("focused")

          itemTop = $(items[index]).parent().offset().top
          scrollTop = $(".topic_menu").scrollTop()
          itemFromTop = $(".topic_menu").offset().top - itemTop
          scrollTarget = Math.min(scrollTop - itemFromTop, scrollTop)
          scrollTarget = Math.max(scrollTop - itemFromTop - $(".topic_menu").height() + $(items[index]).height() + 20, scrollTarget)
          $(".topic_menu").scrollTop(scrollTarget)
