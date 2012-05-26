$ ->
  $.ajaxSetup
    headers : { 'X-CSRFToken': $.cookie 'csrftoken' }

  Calculator.bind()
  Courseware.bind()
  FeedbackForm.bind()
  $("a[rel*=leanModal]").leanModal()
