$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  Calculator.bind()
  FeedbackForm.bind()
  $("a[rel*=leanModal]").leanModal()
