class LibraryEntry extends Backbone.Model
  # declare the basic schema of this model
  defaults:
    id: null
    thumb_url: null
    url: null
    display_name: null
    upload_date: null
    markup: null
    mime_type: null

# this is the collection of assets
class LibraryCollection extends Backbone.Collection
  url: '/assets/'
  model: LibraryEntry

  initialize: (course_location) ->
    # the collection fetch url is /assets/<location
    @url = @url + course_location

# this is the main Backbone View which encompasses the entire
# asset window
class CMS.Views.AssetWidget extends Backbone.View
  initialize: ->
    # the editor is passed in by the caller, we need this so we can inject content into it
    # when we pick the asset to insert
    @editor = @options.editor

    # This subview covers the list of assets
    @library = new CMS.Views.AssetWidget.Library(
      el: @$('.library')
      model: @model
      assetWidget: @
    )

    # this subview covers the upload form
    @uploadForm = new CMS.Views.AssetWidget.UploadForm(
      el: @$('.upload-form')
      model: @model
      assetWidget: @
    )

  insertAssetAndClose: (markup) ->
    @editor.focus()
    @editor.selection.setContent(markup)
    @close()

  close: ->
    @$el.remove();
    # modalCover is defined in html-editor.js
    $modalCover.css('z-index', '1000');  

  openUploadDialog: ->
    @library.$el.hide()
    @uploadForm.$el.show()

  closeUploadDialog: ->
    @library.$el.show()
    @uploadForm.$el.hide()



class CMS.Views.AssetWidget.Library extends Backbone.View
  events:
    "click .upload-button": 'clickUploadButton'
    "keyup .search" : 'searchBarChange'

  initialize: ->
    @assetWidget = @options.assetWidget    

    @assetList = new CMS.Views.AssetWidget.Library.AssetList(
      el: @$('table')
      sortCol:'date'
      sortOrder: 'desc'
      typeFilter: ''
      itemsPerPage: 15
      widget: @assetWidget
      model: @model
    )

  clickUploadButton: (event) ->
    event.preventDefault()
    @assetWidget.openUploadDialog()

  searchBarChange: (event) ->
    @assetList.loadList


class CMS.Views.AssetWidget.Library.AssetItem extends Backbone.View
  events:
    "click .insert-asset-button": 'clickInsertAssetButton'

  initialize: ->
    @widget = @options.widget

  clickInsertAssetButton: ->
    @widget.insertAssetAndClose(@model.get('markup'))


class CMS.Views.AssetWidget.Library.AssetList extends Backbone.View
  initialize: ->
    @widget = @options.widget

    # this is how to tie in Underscore to render the templates
    _.bindAll @

    @sortCol = @options.sortCol
    @sortOrder = @options.sortOrder
    @typeFilter = @options.typeFilter
    @itemPerPage = @options.itemsPerPage
    @pageNum = 1

    # set up the collection data model
    @collection = new LibraryCollection(@model.get('course_location'))

    # set up a callback when something is added to the collection
    # @collection.bind 'add', @renderItem

    # make the trip to the server to populate the collection
    @collection.fetch(
      success: @render
    )   

  render: ->
    @collection.models.forEach(@renderItem)
    return

  renderItem: (item) ->
    template = _.template $('#asset-library-entry').html()
    html = template(item.toJSON())
    $tbody = $(@el).find('tbody')
    $tbody.append html

    $_el = $tbody.find('[data-id="' + item.id + '"]')
    new CMS.Views.AssetWidget.Library.AssetItem(
      el: $_el
      model: item
      widget: @widget
    )
    return


class CMS.Views.AssetWidget.UploadForm extends Backbone.View
  events:
    "click .close-button" : 'closeUploadForm'

  initialize: ->
    @assetWidget = @options.assetWidget

  closeUploadForm: (event) ->
    event.preventDefault()
    @assetWidget.closeUploadDialog()


