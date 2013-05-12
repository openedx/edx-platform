class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'li'
  className: 'component'

  events:
    "click .component-editor .cancel-button": 'clickCancelButton'
    "click .component-editor .save-button": 'clickSaveButton'
    "click .component-actions .edit-button": 'clickEditButton'
    "click .component-actions .delete-button": 'onDelete'
    "click .mode .not-set": 'clickModeButton'

  initialize: ->
    @onDelete = @options.onDelete
    @render()

  $component_editor: => @$el.find('.component-editor')

  loadDisplay: ->
    XModule.loadModule(@$el.find('.xmodule_display'))

  loadEdit: ->
    if not @module
      @module = XModule.loadModule(@$el.find('.xmodule_edit'))
      # At this point, metadata-edit.html will be loaded, and the metadata (as JSON) is available.
      metadataEditor = @$el.find('.metadata_edit')
      @metadataEditor = new CMS.Views.Metadata.Editor({
          el: metadataEditor,
          model: new CMS.Models.MetadataEditor(metadataEditor.data('metadata'))
          });

  changedMetadata: ->
    return @metadataEditor.getModifiedMetadataValues()

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

    analytics.track "Saved Module",
      course: course_location_analytics
      id: _this.model.id

    data.metadata = _.extend(data.metadata || {}, @changedMetadata())
    @hideModal()
    @model.save(data).done( =>
    #   # showToastMessage("Your changes have been saved.", null, 3)
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
    @hideModal()

  hideModal: ->
    $modalCover.hide()
    $modalCover.removeClass('is-fixed')

  clickEditButton: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    $modalCover.show().addClass('is-fixed')
    @$component_editor().slideDown(150)
    @loadEdit()

  clickModeButton: (event) ->
    event.preventDefault()
    @$el.removeClass('not-set')
    @$el.addClass('is-set')
