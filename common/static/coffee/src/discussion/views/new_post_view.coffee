if Backbone?
  class @NewPostView extends Backbone.View

      initialize: () ->
          @dropdownButton = @$(".topic_dropdown_button")
          @topicMenu      = @$(".topic_menu_wrapper")

          @menuOpen = @dropdownButton.hasClass('dropped')

          @topicId    = @$(".topic").first().data("discussion_id")
          @topicText  = @getFullTopicName(@$(".topic").first())

          @maxNameWidth = 100
          @setSelectedTopic()

          DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "new-post-body"
          
          @$(".new-post-tags").tagsInput DiscussionUtil.tagsInputOptions()
          
          if @$($(".topic_menu li a")[0]).attr('cohorted') != "True"
            $('.choose-cohort').hide();
          
            
          
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
          @maxNameWidth = @dropdownButton.width() * 0.9

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
              if $target.attr('cohorted') == "True"
                $('.choose-cohort').show();
              else
                $('.choose-cohort').hide();
              

      setSelectedTopic: ->
          @dropdownButton.html(@fitName(@topicText) + ' <span class="drop-arrow">▾</span>')

      getFullTopicName: (topicElement) ->
          name = topicElement.html()
          topicElement.parents('ul').not('.topic_menu').each ->
              name = $(this).siblings('a').html() + ' / ' + name
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
              partialName = "... / " + path.join(" / ")
              if  @getNameWidth(partialName) < @maxNameWidth
                  return partialName

          rawName = path[0]

          name = "... / " + rawName

          while @getNameWidth(name) > @maxNameWidth
              rawName = rawName[0...rawName.length-1]
              name =  "... / " + rawName + " ..."

          return name


      createPost: (event) ->
          event.preventDefault()
          title   = @$(".new-post-title").val()
          body    = @$(".new-post-body").find(".wmd-input").val()
          tags    = @$(".new-post-tags").val()
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
                  tags: tags
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
                  @$(".new-post-tags").val("")
                  @$(".new-post-tags").importTags("")
                  @$(".wmd-preview p").html("")
                  @collection.add thread

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
