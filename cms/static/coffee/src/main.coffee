@CMS =
  Models: {}
  Views: {}

  start: ->
    new CMS.Views.Course el: $('section.main-container')

_.extend CMS, Backbone.Events

$ ->
  $.ajaxSetup
      headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  CMS.start()
