$(document).on('click', 'section.sa-wrapper input#show', ( ->
  root = location.protocol + "//" + location.host
  post_url=$('section.sa-wrapper input#show').attr('url')
  alert(post_url)
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_show"
  alert(final_url)

  $.post final_url, answer, (response) ->
  if response.success
    $('p.rubric').replace(response.rubric)

  alert("save")
));

$(document).on('click', 'section.sa-wrapper input#save', ( ->
  answer=$('section.sa-wrapper input#answer').val()
  alert(answer)
  assessment=0
  assessment_correct=$('section.sa-wrapper input#assessment_correct').val()
  alert(assessment_correct)
  assessment_incorrect=$('section.sa-wrapper input#assessment_incorrect').val()
  alert(assessment_incorrect)

  root = location.protocol + "//" + location.host
  post_url=$('section.sa-wrapper input#show').attr('url')
  alert(post_url)
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_save"
  alert(final_url)

  $.post final_url, answer, (response) ->
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

