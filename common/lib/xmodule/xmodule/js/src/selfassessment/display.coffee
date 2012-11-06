wrapper_name='section.sa-wrapper'

$(document).on('click', "#{wrapper_name} input#show", ( ->
  post_url=$("#{wrapper_name} input#ajax_url").attr('url')
  final_url="#{post_url}/sa_show"
  answer=$("#{wrapper_name} textarea#answer").val()
  $.post final_url, {'student_answer' : answer }, (response) ->
    if response.success
      $("#{wrapper_name} input#show").remove()
      $("#{wrapper_name} textarea#answer").remove()
      $("#{wrapper_name} p#rubric").append("Your answer: #{answer}")
      $("#{wrapper_name} p#rubric").append(response.rubric)
    else
      $("#{wrapper_name} input#show").remove()
      $("#{wrapper_name} p#rubric").append(response.message)
));

$(document).on('click', "#{wrapper_name} input#save", ( ->
  assessment=$("#{wrapper_name} #assessment").find(':selected').text()
  post_url=$("#{wrapper_name} input#ajax_url").attr('url')
  final_url="#{post_url}/sa_save"
  hint=$("#{wrapper_name} textarea#hint").val()
  $.post final_url, {'assessment':assessment, 'hint':hint}, (response) ->
    if response.success
      $("#{wrapper_name} p#save_message").append(response.message)
      $("#{wrapper_name} input#save").remove()
));
