sa_wrapper_name='section.sa-wrapper'

$(document).on('click', "#{sa_wrapper_name} input#show", ( ->
  post_url=$("#{sa_wrapper_name} input#ajax_url").attr('url')
  final_url="#{post_url}/sa_show"
  answer=$("#{sa_wrapper_name} textarea#answer").val()
  $.post final_url, {'student_answer' : answer }, (response) ->
    if response.success
      $("#{sa_wrapper_name} input#show").remove()
      $("#{sa_wrapper_name} textarea#answer").remove()
      $("#{sa_wrapper_name} p#rubric").append("Your answer: #{answer}")
      $("#{sa_wrapper_name} p#rubric").append(response.rubric)
    else
      $("#{sa_wrapper_name} input#show").remove()
      $("#{sa_wrapper_name} p#rubric").append(response.message)
));

$(document).on('click', "#{sa_wrapper_name} input#save", ( ->
  assessment=$("#{sa_wrapper_name} #assessment").find(':selected').text()
  post_url=$("#{sa_wrapper_name} input#ajax_url").attr('url')
  final_url="#{post_url}/sa_save"
  hint=$("#{sa_wrapper_name} textarea#hint").val()
  $.post final_url, {'assessment':assessment, 'hint':hint}, (response) ->
    if response.success
      $("#{sa_wrapper_name} p#save_message").append(response.message)
      $("#{sa_wrapper_name} input#save").remove()
));
