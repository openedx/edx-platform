$(document).on('click', 'section.sa-wrapper input#show', ( ->
  root = location.protocol + "//" + location.host
  post_url=$('section.sa-wrapper input#show').attr('url')
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_show"
  answer=$('section.sa-wrapper input#answer').val()
  alert(answer)
  alert(final_url)

  $.post final_url, answer, (response) ->
    alert("posted")
    if response.success
      alert(response.rubric)
      $('section.sa-wrapper p#rubric').append(response.rubric)
));

$(document).on('click', 'section.sa-wrapper input#save', ( ->
  answer=$('section.sa-wrapper input#answer').val()
  alert(answer)
  assessment=0
  assessment_correct=$('section.sa-wrapper input#assessment_correct').selected()
  alert(assessment_correct)
  assessment_incorrect=$('section.sa-wrapper input#assessment_incorrect').selected()
  alert(assessment_incorrect)

  root = location.protocol + "//" + location.host
  post_url=$('section.sa-wrapper input#show').attr('url')
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_save"

  $('section.sa-wrapper input#assessment option').each( ->
    if (this.selected)
      alert('this option is selected')
    else
      alert('this is not')
  );

  $.post final_url, answer, (response) ->
  if response.success
    $('section.sa_wrapper p#save_message').replace(response.message)

  alert("save")
));
