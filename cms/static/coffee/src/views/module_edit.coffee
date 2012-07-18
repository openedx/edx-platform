class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  events:
    'click .cancel': 'cancel'
    'click .module-edit': 'editSubmodule'
    'click .save-update': 'save'

  initialize: ->
    @$el.load @model.editUrl(), =>
      @model.loadModule(@el)
      @$el.find('.preview').children().each (idx, previewEl) =>
          @model.loadPreview(previewEl)

  save: (event) ->
    event.preventDefault()
    @model.save().success(->
      alert("Your changes have been saved.")
    ).error(->
      alert("There was an error saving your changes. Please try again.")
    )

  cancel: (event) ->
    event.preventDefault()
    CMS.popView()

  editSubmodule: (event) ->
    event.preventDefault()
    previewType = $(event.target).data('preview-type')
    moduleType = $(event.target).data('type')
    CMS.pushView new CMS.Views.ModuleEdit
        model: new CMS.Models.Module
            id: $(event.target).data('id')
            type: if moduleType == 'None' then null else moduleType
            previewType: if previewType == 'None' then null else previewType
