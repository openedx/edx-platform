$(document).on('click', 'section.sa-wrapper input#show', ( ->
  post_url=$('section.sa-wrapper input#ajax_url').attr('url')
  final_url="#{post_url}/sa_show"
  answer=$('section.sa-wrapper textarea#answer').val()
  $.post final_url, answer, (response) ->
    if response.success
      $('section.sa-wrapper input#show').remove()
      $('section.sa-wrapper textarea#answer').remove()
      $('section.sa-wrapper p#rubric').append("Your answer: #{answer}")
      $('section.sa-wrapper p#rubric').append(response.rubric)
    else
      $('section.sa-wrapper p#rubric').append(response.message)
));

$(document).on('click', 'section.sa-wrapper input#save', ( ->
  assessment=$('section.sa-wrapper #assessment').find(':selected').text()
  post_url=$('section.sa-wrapper input#ajax_url').attr('url')
  final_url="#{post_url}/sa_save"
  $.post final_url, assessment, (response) ->
    if response.success
      $('section.sa-wrapper p#save_message').append(response.message)
      $('section.sa-wrapper input#save').remove()
));
