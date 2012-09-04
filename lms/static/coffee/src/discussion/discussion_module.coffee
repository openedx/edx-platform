if Backbone?
  class @DiscussionModuleView extends Backbone.View
    events:
      "click .discussion-show": "toggleDiscussion"
    toggleDiscussion: (event) ->
      if @showed
        @$("section.discussion").hide()
        $(event.target).html("Show Discussion")
        @showed = false
      else
        if @retrieved
          @$("section.discussion").show()
          $(event.target).html("Hide Discussion")
          @showed = true
        else
          $elem = $(event.target)
          discussion_id = $elem.attr("discussion_id")
          url = DiscussionUtil.urlFor 'retrieve_discussion', discussion_id
          DiscussionUtil.safeAjax
            $elem: $elem
            $loading: $elem
            url: url
            type: "GET"
            dataType: 'json'
            success: (response, textStatus) =>
              #@$el.append(response.html)
              window.user = new DiscussionUser(response.user_info)
              $(event.target).html("Hide Discussion")
              discussion = new Discussion()
              discussion.reset(response.discussion_data, {silent: false})
              $discussion = $(Mustache.render $("script#_inline_discussion").html(), {'threads':response.discussion_data})
              $(".discussion-module").append($discussion)
              discussion.each (thread) ->
                element = $("article#thread_#{thread.id}")
                dtv = new DiscussionThreadView el: element, model: thread
                dtv.render()
              DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
              @retrieved = true
              @showed = true
