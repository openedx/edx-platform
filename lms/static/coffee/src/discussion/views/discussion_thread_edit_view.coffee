if Backbone?
  class @DiscussionThreadEditView extends Backbone.View

    events:
      "click .post-update": "update"
      "click .post-cancel": "cancel_edit"
      "click .topic_dropdown_button":    "toggleTopicDropdown"
      "click  .topic_menu_wrapper":       "setTopic"
      "click  .topic_menu_search":        "ignoreClick"
      "keyup .form-topic-drop-search-input": DiscussionFilter.filterDrop      

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()
      @maxNameWidth = 400
      
    ignoreClick: (event) ->
      event.stopPropagation()
      
      
    initElements: ->
      @dropdownButton = @$(".topic_dropdown_button_edit")
      @topicMenu      = @$(".topic_menu_wrapper")
      @menuOpen = @dropdownButton.hasClass('dropped')      
      #@topicText  = @getFullTopicName(@$(".topic").first())
      $target = @$("#"+@model.get("commentable_id"))
      if $target.data('discussion_id')
          @topicText = $target.html()
          @topicText  = @getFullTopicName($target)
          @topicId   = $target.data('discussion_id')
          @setSelectedTopic()      
      
    render: ->
      @template = _.template($("#thread-edit-template").html())
      
      @$el.html(@template(@model.toJSON()))
      @initElements()
      @delegateEvents()
      DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "edit-post-body"
      @$(".edit-post-tags").tagsInput DiscussionUtil.tagsInputOptions()
      @

    update: (event) ->
      @trigger "thread:update", event

    cancel_edit: (event) ->
      @trigger "thread:cancel_edit", event

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
              

      setSelectedTopic: ->
          @dropdownButton.html(@fitName(@topicText) + ' <span class="drop-arrow">▾</span>')
          #now we have to set the form's hidden commentable_id so when it submits
          #it has the new value
          $hidden = $("#commentable-id-edit")
          if $hidden
            $hidden.val(@topicId)
            $hidden.attr('display_name',@topicText);

      getFullTopicName: (topicElement) ->
          name = topicElement.html()
          topicElement.parents('ul').not('.topic_menu').each ->
              name = $(this).siblings('a').html() + ' / ' + name
          return name      
          
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