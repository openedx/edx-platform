class CMS.Views.WeekEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  initialize: ->
    CMS.trigger('week.edit')
