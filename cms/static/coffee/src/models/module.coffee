class CMS.Models.Module extends Backbone.Model
  url: '/save_item'
  defaults:
    data: ''

  loadModule: (element) ->
    try
      @module = new window[@get('type')](element)
    catch TypeError
      console.error "Unable to load #{@get('type')}." if console

  editUrl: ->
    "/edit_item?#{$.param(id: @get('id'))}"

  save: (args...) ->
    @set(data: JSON.stringify(@module.save())) if @module
    super(args...)
