class CMS.Views.HTMLModuleEdit extends CMS.Views.ModuleEdit
	events:
		"click .component-actions .edit-button": 'clickEditButton'
		"click .component-actions .delete-button": 'onDelete'

	initialize: ->
		@onDelete = @options.onDelete
		super(@options)

	clickEditButton: (event) ->
		event.preventDefault()
		@enterEditMode()

	enterEditMode: ->
		$preview = @$el.find('.xmodule_display')
		if $preview
			html = $preview.html()

		@$componentItem = $('<li>').addClass('editing')
		@$editor = $($('#html-editor').html())
		# initHTMLEditor is in a separate .js file
		# id here is the location_id
		initHTMLEditor(@$editor, html, @model.get('course_location'))
		@$editor.find('.cancel-button').bind('click', @closeEditor)
		@$editor.find('.save-button').bind('click', @saveEditor)
		
		$componentActions = $($('#component-actions').html())
		@$componentItem.append(@$editor)
		@$componentItem.append($componentActions)
		@$componentItem.hide()
		@$el.before(@$componentItem)
		@$componentItem.show()

		# $modalCover is defined in base.js
		$modalCover.fadeIn(200)
		$modalCover.bind('click', @closeEditor)

	closeEditor: (event) =>
		@$componentItem.remove()
		@$editor.slideUp(150)
		$modalCover.fadeOut(150)
		$modalCover.unbind('click', @closeEditor)
		@$editor.slideUp(150)
		@$componentItem.removeClass('editing')  

	saveEditor: (event) =>
		html = getHTMLContent()

		if not @model.id
			@cloneTemplate(
				@options.parent,
				'i4x://edx/templates/html/Empty',
				html
			)
			@closeEditor()
		else
			data = 
				data: html

			@model.save(data).done( =>
				@$el.find('.xmodule_display').html(html)
				@$componentItem.remove()
				@closeEditor()
			).fail( =>
     			showToastMessage("There was an error saving your changes. Please try again.", null, 3)
    		)
