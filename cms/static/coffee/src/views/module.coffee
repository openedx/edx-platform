class CMS.Views.Module extends Backbone.View
  events:
    "click .module-edit": "edit"

  edit: (event) =>
    event.preventDefault()
    previewType = @$el.data('preview-type')
    moduleType = @$el.data('type')
    CMS.replaceView new CMS.Views.ModuleEdit
      model: new CMS.Models.Module
        id: @$el.data('id')
        type: if moduleType == 'None' then null else moduleType
        previewType: if previewType == 'None' then null else previewType

