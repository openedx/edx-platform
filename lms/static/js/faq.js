$(document).ready(function() {
    var open_question = "";
    var question_id;

    $('.response').click(function(){
      $(this).toggleClass('opened');
      answer = $(this).find(".answer");
      answer.slideToggle('fast');
    });
});
