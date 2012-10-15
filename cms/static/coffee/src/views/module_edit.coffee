class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'li'
  className: 'component'

  events:
    "click .component-editor .cancel-button": 'clickCancelButton'
    "click .component-editor .save-button": 'clickSaveButton'
    "click .component-actions .edit-button": 'clickEditButton'
    "click .component-actions .delete-button": 'onDelete'

  initialize: ->
    @onDelete = @options.onDelete
    @render()

  $component_editor: => @$el.find('.component-editor')

  loadDisplay: ->
       XModule.loadModule(@$el.find('.xmodule_display'))

  loadEdit: ->
    if not @module
      @module = XModule.loadModule(@$el.find('.xmodule_edit'))

  metadata: ->
    # cdodge: package up metadata which is separated into a number of input fields
    # there's probably a better way to do this, but at least this lets me continue to move onwards
    _metadata = {}

    $metadata = @$component_editor().find('.metadata_edit')

    if $metadata
      # walk through the set of elments which have the 'xmetadata_name' attribute and
      # build up a object to pass back to the server on the subsequent POST
      _metadata[$(el).data("metadata-name")] = el.value for el in $('[data-metadata-name]', $metadata)

    return _metadata

  cloneTemplate: (parent, template) ->
    $.post("/clone_item", {
      parent_location: parent
      template: template
    }, (data) => 
      @model.set(id: data.id)
      @$el.data('id', data.id)
      @render()
    )

  render: ->
    if @model.id
      @$el.load("/preview_component/#{@model.id}", =>
        @loadDisplay()
        @delegateEvents()
      )

  clickSaveButton: (event) =>
    event.preventDefault()
    data = @module.save()
    data.metadata = @metadata()
    @model.save(data).done( =>
      showToastMessage("Your changes have been saved.", null, 3)
      @module = null
      @render()
      @$el.removeClass('editing')
    ).fail( ->
      showToastMessage("There was an error saving your changes. Please try again.", null, 3)
    )

  clickCancelButton: (event) ->
    event.preventDefault()
    @$el.removeClass('editing')
    @$component_editor().slideUp(150)

  clickEditButton: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    @$component_editor().slideDown(150)
    @loadEdit()
