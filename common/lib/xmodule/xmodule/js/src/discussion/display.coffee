class @InlineDiscussion
  constructor: (element) ->
    @el = $(element).find('.discussion-module')
    @view = new DiscussionModuleView(el: @el)
