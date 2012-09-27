class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'div'
  className: 'xmodule_edit'

  initialize: ->
    @module = @options.module
    @module.onUpdate(@save)

    @setEvents()

  $component_editor: -> @$el.find('.component-editor')

  setEvents: ->
    id = @$el.data('id')

    @events = {}
    @events["click .component-editor[data-id=#{ id }] .cancel-button"] = 'clickCancelButton'
    @events["click .component-editor[data-id=#{ id }] .save-button"] = 'clickSaveButton'
    @events["click .component-actions[data-id=#{ id }] .edit-button"] = 'clickEditButton'

    @delegateEvents()

  metadata: ->
    # cdodge: package up metadata which is separated into a number of input fields
    # there's probably a better way to do this, but at least this lets me continue to move onwards
    _metadata = {}

    $metadata = @$component_editor().find('.metadata_edit')

    if $metadata
      # walk through the set of elments which have the 'xmetadata_name' attribute and
      # build up a object to pass back to the server on the subsequent POST
      _metadata[$(el).data("metadata-name")] = el.value for el in $('[data-metadata-name]', $metadata)

    _metadata

  save: (data) =>
    @model.set(data)
    @model.save().done((preview) =>
      alert("Your changes have been saved.")

      $preview = $(preview)
      @$el.replaceWith($preview)
      @setElement($preview)
      @module.constructor(@$el)
      XModule.loadModules(@$el)

    ).fail( ->
      alert("There was an error saving your changes. Please try again.")
    )

  clickSaveButton: (event) =>
    event.preventDefault()
    data = @module.save()
    data.metadata = @metadata()

    @save(data)

  clickCancelButton: (event) ->
    event.preventDefault()
    @$el.removeClass('editing')
    @$component_editor().slideUp(150)

  clickEditButton: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    @$component_editor().slideDown(150)
