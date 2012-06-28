class CMS.Models.Module extends Backbone.Model
  editUrl: ->
    "/edit_item?id=#{@get('id')}"
