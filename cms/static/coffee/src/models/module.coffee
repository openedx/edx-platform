class CMS.Models.Module extends Backbone.Model
  url: '/save_item'
  defaults:
    data: ''

  loadModule: (element) ->
    moduleType = @get('type')

    try
      @module = if moduleType? then new window[moduleType](element) else null
    catch error
      console.error "Unable to load #{moduleType}: #{error.message}" if console

  loadPreview: (element) ->
    previewType = @get('previewType')

    try
      @previewModule = if previewType? then new window[previewType](element) else null
    catch error
      console.error "Unable to load #{previewType}: #{error.message}" if console

  editUrl: ->
    "/edit_item?#{$.param(id: @get('id'))}"

  save: (args...) ->
    @set(data: JSON.stringify(@module.save())) if @module
    super(args...)
