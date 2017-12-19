class @InlineDiscussion extends XModule.Descriptor
  constructor: (element) ->
    @el = $(element).find('.discussion-module')
    @view = new DiscussionInlineView(el: @el)
