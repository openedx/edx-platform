$(document).on('click', 'section.sa-wrapper input#show', ( ->
  post_url=$('section.sa-wrapper input#show').attr('url')
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_show"
  answer=$('section.sa-wrapper textarea#answer').val()
  $.post final_url, answer, (response) ->
    if response.success
      $('section.sa-wrapper input#show').remove()
      $('section.sa-wrapper textarea#answer').remove()
      $('section.sa-wrapper p#rubric').append(answer)
      $('section.sa-wrapper p#rubric').append(response.rubric)
));

$(document).on('click', 'section.sa-wrapper input#save', ( ->
  assessment_correct=$('section.sa-wrapper #assessment').find(':selected').text()
  post_url=$('section.sa-wrapper input#save').attr('url')
  final_url="/courses/MITx/6.002x/2012_Fall/modx/#{post_url}/sa_save"
  $.post final_url, assessment_correct, (response) ->
    if response.success
      $('section.sa-wrapper p#save_message').append(response.message)
      $('section.sa-wrapper input#save').remove()
));
