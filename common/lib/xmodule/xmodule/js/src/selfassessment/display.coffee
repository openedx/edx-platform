
#@$('section.action input.check').click @check
$('input#show').click(@show)
#$('#save').click(function -> alert('save'))

$(document).on('click', 'input#save', ( ->
  answer=$('#answer').text()
  $.postWithPrefix "modx/6.002x/sa_save", answer, (response) ->
  if response.success
    $('p.rubric').replace(response.rubric)

  alert("save")
));

show: =>
  alert("show")
  #$.postWithPrefix "/sa_show", (response) =>
  #  answers = response.answers
  #  @el.addClass 'showed'

save: =>
  alert("save")

alert($('input#save').attr('url'))

