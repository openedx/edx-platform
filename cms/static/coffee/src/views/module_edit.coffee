class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'li'
  className: 'component'

  events:
    "click .component-editor .cancel-button": 'clickCancelButton'
    "click .component-editor .save-button": 'clickSaveButton'
    "click .component-actions .edit-button": 'clickEditButton'


  initialize: ->
    @module = @options.module
    @render()

  $component_editor: => @$el.find('.component-editor')

  loadDisplay: ->
       XModule.loadModule(@$el.find('.xmodule_display'))

  loadEdit: ->
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

  cloneTemplate: (template) ->
    $.post("/clone_item", {
      parent_location: @$el.parent().data('id')
      template: template
    }, (data) => 
      @model.set(id: data.id)
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
      alert("Your changes have been saved.")

      @render()
      @$el.removeClass('editing')
    ).fail( ->
      alert("There was an error saving your changes. Please try again.")
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
