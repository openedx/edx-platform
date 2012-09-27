class CMS.Models.Module extends Backbone.Model
  url: '/save_item'
  defaults:
    data: ''
    children: ''
    metadata: {}

  initialize: (attributes) ->
    @module = attributes.module
    @unset('module')
    delete attributes.module
    super(attributes)
