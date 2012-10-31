show: =>
  Logger.log 'sa_show', problem: @id
  $.postWithPrefix "#{@url}/sa_show", (response) =>
    answers = response.answers
    $.each answers, (key, value) =>
      if $.isArray(value)
        for choice in value
          @$("label[for='input_#{key}_#{choice}']").attr correct_answer: 'true'
      else
        answer = @$("#answer_#{key}, #solution_#{key}")
        answer.html(value)
        Collapsible.setCollapsibles(answer)

    @$('.show').val 'Hide Answer'
    @el.addClass 'showed'

save: =>
  Logger.log 'sa_save', @answers
  $.postWithPrefix "#{@url}/sa_save", @answers, (response) =>
    if response.success
     @$('p.rubric').replace(response.rubric)
