class CMS.Views.ModuleSpeedEdit extends CMS.Views.ModuleEdit
  events:
    "click .component-actions .edit-button": 'clickEditButton'
    "click .component-actions .delete-button": 'onDelete'

  initialize: ->
    @onDelete = @options.onDelete
    @parent = @options.parent
    super(@options)

  clickEditButton: ->
    @enterEditMode()

  enterEditMode: ->
    @$editorEl = $($('#problem-editor').html())

    # Toggle our class
    @$el.addClass('editing')

    # We put the editor dialog in a separate Backbone view
    @$editor = new CMS.Views.SpeedEditor(
      el: @$editorEl
      widget: @   # pass along a callback
      parent: @parent
      model: @model
    )

    $componentActions = $($('#component-actions').html())
    @$el.append(@$editorEl)
    @$el.append($componentActions)
    @$el.show()

    # $modalCover is defined in base.js
    $modalCover.fadeIn(200)

  onCloseEditor: ->
    @exitEditMode()
    @$el.remove()

  onSaveEditor: ->
    # note, we need to nest the whole XML inside a <problem></problem>
    xml = '<problem>\n'+getXMLContent()+'</problem>'

    metadata = {'markdown_source': getMarkdownContent()}

    if not @model.id
      @cloneTemplate(
        @options.parent,
        'i4x://edx/templates/problem/Empty',
        xml,
        metadata
      )
      @exitEditMode()
    else
      data = 
        data: xml

      @model.save(data).done( ->
        @exitEditMode()
      ).fail( =>
          showToastMessage("There was an error saving your changes. Please try again.", null, 3)
        )

  exitEditMode: ->
    $modalCover.fadeOut(150)
    @$editorEl.remove()
    @$el.removeClass('editing')

class CMS.Views.SpeedEditor extends Backbone.View
  events:
    "click .cancel-button": 'closeEditor'
    "click .save-button": 'saveEditor'

  initialize: ->
    @$preview = $($('#problem-preview').html())
    initProblemEditors(@$el, @$preview)
    @$el.append(@$preview)

  closeEditor: (event) ->
    @$el.slideUp(150)
    if @options.widget
      @options.widget.onCloseEditor()

  saveEditor: (event) ->
    if @options.widget
      @options.widget.onSaveEditor()

