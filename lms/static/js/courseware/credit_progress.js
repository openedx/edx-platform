$(document).ready(function() {
    $('.detail-collapse').click(function(){
        $('.requirement-container').toggleClass('is-hidden');
        $(this).find('.fa').toggleClass('fa-caret-down fa-caret-up');
        $(this).find('span').text(function(i, text){
          return text === "Expand for details" ? "Collapse" : "Expand for details";
        });
    });

});
