class CMS.Models.NewModule extends Backbone.Model
  url: '/clone_item'

  newUrl: ->
    "/new_item?#{$.param(parent_location: @get('parent_location'))}"
