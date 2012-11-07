class CMS.Models.Module extends Backbone.Model
  url: '/save_item'
  defaults:
    data: ''
    children: ''
    metadata: {}

  loadModule: (element) ->
    elt = $(element).find('.xmodule_edit').first()
    @module = XModule.loadModule(elt)
    # find the metadata edit region which should be setup server side,
    # so that we can wire up posting back those changes
    @metadata_elt = $(element).find('.metadata_edit')

  editUrl: ->
    "/edit_item?#{$.param(id: @get('id'))}"

  save: (args...) ->
    @set(data: @module.save()) if @module
    # cdodge: package up metadata which is separated into a number of input fields
    # there's probably a better way to do this, but at least this lets me continue to move onwards
    if @metadata_elt
      _metadata = {}
      # walk through the set of elments which have the 'xmetadata_name' attribute and
      # build up a object to pass back to the server on the subsequent POST
      _metadata[$(el).data("metadata-name")]=el.value for el in $('[data-metadata-name]', @metadata_elt)
      @set(metadata: _metadata)
    super(args...)
