class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'div'
  className: 'xmodule_edit'

  initialize: ->
    @delegate()

    @$component_editor = @$el.find('.component-editor')
    @$metadata = @$component_editor.find('.metadata_edit')

  delegate: ->
    id = @$el.data('id')

    events = {}
    events["click .component-editor[data-id=#{ id }] .cancel-button"] = 'cancel'
    events["click .component-editor[data-id=#{ id }] .save-button"] = 'save'
    events["click .component-actions[data-id=#{ id }] .edit-button"] = 'edit'

    @delegateEvents(events)

  metadata: ->
    # cdodge: package up metadata which is separated into a number of input fields
    # there's probably a better way to do this, but at least this lets me continue to move onwards
    _metadata = {}

    if @$metadata
      # walk through the set of elments which have the 'xmetadata_name' attribute and
      # build up a object to pass back to the server on the subsequent POST
      _metadata[$(el).data("metadata-name")] = el.value for el in $('[data-metadata-name]', @$metadata)

    _metadata

  save: (event) =>
    event.preventDefault()
    @model.save(
      metadata: @metadata()
    ).done((preview) =>
      alert("Your changes have been saved.")
      
      new_el = $(preview)
      @$el.replaceWith(new_el)
      @$el = new_el

      @delegate()

      @model.module = XModule.loadModule(@$el)
      XModule.loadModules(@$el)
    ).fail( ->
      alert("There was an error saving your changes. Please try again.")
    )

  cancel: (event) ->
    event.preventDefault()
    @$el.removeClass('editing')
    @$component_editor.slideUp(150)

  edit: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    @$component_editor.slideDown(150)
