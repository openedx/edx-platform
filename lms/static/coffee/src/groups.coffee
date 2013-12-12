###
Groups

A simple test to see if this CoffeeScript file gets compiled.
###

class @GroupsForm
  constructor: ->
    $('#join_button').click ->
      data =
        url: window.location.href
      window.location = data.url
      $.postWithPrefix '/send_feedback', data, ->
        $('#join_div').html 'Code not valid.'
      ,'json'