class CMS.Models.Module extends Backbone.Model
  url: '#{@course_id}/save_item'

  defaults:
    courseId: null
