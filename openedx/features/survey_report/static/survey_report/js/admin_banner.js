$(document).ready(function(){
  $('#dismissButton').click(function() {
    $('#originalContent').slideUp('slow', function() {
      // If you want to do something after the slide-up, do it here.
      // For example, you can hide the entire div:
      // $(this).hide();
    });
  });
  // When the form is submitted
  $("#survey_report_form").submit(function(event){
    event.preventDefault();  // Prevent the form from submitting traditionally

    // Make the AJAX request
    $.ajax({
      url: $(this).attr("action"),
      type: $(this).attr("method"),
      data: $(this).serialize(),
      success: function(response){
        // Hide the original content block
        $("#originalContent").slideUp(400, function() {
          //$(this).css('display', 'none');
          // Show the thank-you message block with slide down effect
          $("#thankYouMessage").slideDown(400, function() {
            // Wait for 3 seconds (3000 milliseconds) and then slide up the thank-you message
            setTimeout(function() {
              $("#thankYouMessage").slideUp(400);
              }, 3000);
          });
        });
        },
      error: function(error){
        // Handle any errors
        console.error("Error sending report:", error);
      }
    });
  });
});
