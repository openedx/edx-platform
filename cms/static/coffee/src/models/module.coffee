class CMS.Models.Module extends Backbone.Model
  initialize: ->
    try
      @module = new window[@get('type')](@get('id'))
    catch TypeError
      console.error "Unable to load #{@get('type')}." if console

  editUrl: ->
    "/edit_item?#{$.param(id: @get('id'))}"
