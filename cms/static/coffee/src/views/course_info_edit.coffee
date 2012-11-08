## Derived from and should inherit from a common ancestor w/ ModuleEdit
class CMS.Views.CourseInfoEdit extends Backbone.View
  tagName: 'div'
  className: 'component'

  events:
    "click .component-editor .cancel-button": 'clickCancelButton'
    "click .component-editor .save-button": 'clickSaveButton'
    "click .component-actions .edit-button": 'clickEditButton'
    "click .component-actions .delete-button": 'onDelete'

  initialize: ->
    @render()

  $component_editor: => @$el.find('.component-editor')

  loadDisplay: ->
       XModule.loadModule(@$el.find('.xmodule_display'))

  loadEdit: ->
    if not @module
      @module = XModule.loadModule(@$el.find('.xmodule_edit'))

  # don't show metadata (deprecated for course_info)
  render: ->
    if @model.id
      @$el.load("/preview_component/#{@model.id}", =>
        @loadDisplay()
        @delegateEvents()
      )

  clickSaveButton: (event) =>
    event.preventDefault()
    data = @module.save()
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

  clickEditButton: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    @$component_editor().slideDown(150)
    @loadEdit()

  onDelete: (event) ->
    # clear contents, don't delete
    @model.definition.data = "<ol></ol>"
    # TODO change label to 'clear'
    
  onNew: (event) ->
  	ele = $(@model.definition.data).find("ol")
  	if (ele)
  		ele = $(ele).first().prepend("<li><h2>" + $.datepicker.formatDate('MM d', new Date()) + "</h2>/n</li>");