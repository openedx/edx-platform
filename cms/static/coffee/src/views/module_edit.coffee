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

      # Load preview modules
      XModule.loadModules('display')
      @$children = @$el.find('#sortable')
      @enableDrag()

  enableDrag: =>
      # Enable dragging things in the #sortable div (if there is one)
      if @$children.length > 0
        @$children.sortable(
          placeholder: "ui-state-highlight"
          update: (event, ui) =>
            @model.set(children: @$children.find('.module-edit').map(
                (idx, el) -> $(el).data('id')
            ).toArray())
        )
        @$children.disableSelection()

  save: (event) =>
    event.preventDefault()
    @model.save().done((previews) =>
      alert("Your changes have been saved.")
      previews_section = @$el.find('.previews').empty()
      $.each(previews, (idx, preview) =>
        preview_wrapper = $('<section/>', class: 'preview').append preview
        previews_section.append preview_wrapper
      )

      XModule.loadModules('display')
    ).fail(->
      alert("There was an error saving your changes. Please try again.")
    )

  cancel: (event) ->
    event.preventDefault()
    CMS.popView()
    @enableDrag()

  editSubmodule: (event) ->
    event.preventDefault()
    previewType = $(event.target).data('preview-type')
    moduleType = $(event.target).data('type')
    CMS.pushView new CMS.Views.ModuleEdit
        model: new CMS.Models.Module
            id: $(event.target).data('id')
            type: if moduleType == 'None' then null else moduleType
            previewType: if previewType == 'None' then null else previewType
    @enableDrag()
